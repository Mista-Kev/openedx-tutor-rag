"""
OpenEdX Course Content Extractor

This script pulls course content from Open edX's MongoDB and indexes it into Qdrant
for our RAG system. The tricky part is understanding how Open edX stores data - they
use something called "Split Mongo" which splits course data across three collections.

We figured this out from the Open edX docs:
https://docs.openedx.org/projects/edx-platform/en/latest/references/docs/xmodule/modulestore/docs/split-mongo.html

The three collections are:
- modulestore.active_versions: tells us which version of each course is "live"
- modulestore.structures: the course tree (chapters > sections > units > blocks)
- modulestore.definitions: the actual content (HTML, video info, etc.)

For transcripts, Open edX uses GridFS (MongoDB's file storage system).
"""

import re
import gridfs
from pymongo import MongoClient

# LlamaIndex handles the chunking and embedding for us
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from qdrant_client import QdrantClient

# our config has the MongoDB and Qdrant connection settings
try:
    from qdrant_rag.config import mongo_config, qdrant_config
except ImportError:
    from config import mongo_config, qdrant_config


def clean_html(html_content: str) -> str:
    """
    Strip HTML tags from content. Open edX stores everything as HTML,
    but we want plain text for the embeddings.
    """
    if not html_content:
        return ""

    # remove all HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)

    # collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text)

    # handle common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')

    return text.strip()


class OpenEdXExtractor:
    """
    Connects to Open edX's MongoDB and extracts course content.

    The connection settings come from Tutor's config - inside the Docker network,
    MongoDB is available at 'mongodb:27017' and the database is called 'openedx'.
    """

    def __init__(self):
        print("Connecting to MongoDB...")
        print(f"   Host: {mongo_config.connection_string}")

        self.client = MongoClient(mongo_config.connection_string)
        self.db = self.client[mongo_config.database]

        # GridFS is where Open edX stores files like transcripts
        self.fs = gridfs.GridFS(self.db)

        # these are the three Split Mongo collections we need
        self.active_versions = self.db["modulestore.active_versions"]
        self.structures = self.db["modulestore.structures"]
        self.definitions = self.db["modulestore.definitions"]

        print("Connected!")

    def get_courses(self) -> list[dict]:
        """
        Get all courses from the database.
        Each course has an org, course code, and run (like a semester).
        """
        courses = []

        for doc in self.active_versions.find():
            # course IDs in Open edX look like: course-v1:OrgName+CourseCode+Run
            course_id = f"course-v1:{doc.get('org')}+{doc.get('course')}+{doc.get('run')}"
            courses.append({
                "course_id": course_id,
                "org": doc.get("org"),
                "course": doc.get("course"),
                "run": doc.get("run"),
            })

        print(f"Found {len(courses)} courses")
        return courses

    def _get_published_structure(self, course_id: str) -> dict | None:
        """
        Get the published version of a course structure.

        This is a two-step lookup:
        1. Find the course in active_versions to get the published version ID
        2. Fetch that version from the structures collection
        """
        # parse the course ID to get org, course, run
        if not course_id.startswith("course-v1:"):
            return None

        parts = course_id[10:].split("+")
        if len(parts) != 3:
            return None

        org, course, run = parts

        # step 1: find active version
        active = self.active_versions.find_one({
            "org": org, "course": course, "run": run
        })

        if not active:
            print(f"Course not found: {course_id}")
            return None

        # step 2: get the published branch ID and fetch the structure
        version_id = active.get("versions", {}).get("published-branch")
        if not version_id:
            return None

        return self.structures.find_one({"_id": version_id})

    def _get_transcript(self, filename: str) -> str:
        """
        Fetch a transcript file from GridFS and clean it up.

        Transcripts are stored as SRT files, so we need to strip out
        the timestamp lines (like "00:00:05,000 --> 00:00:10,000").
        """
        try:
            grid_file = self.fs.find_one({"filename": filename})
            if not grid_file:
                return ""

            content = grid_file.read().decode('utf-8', errors='ignore')

            # remove SRT timestamps and sequence numbers
            content = re.sub(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', '', content)
            content = re.sub(r'^\d+\s*$', '', content, flags=re.MULTILINE)

            # join all the text lines
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            return " ".join(lines)

        except Exception as e:
            print(f"Could not read transcript {filename}: {e}")
            return ""

    def _extract_content(self, block: dict, definitions: dict) -> str:
        """
        Pull the text content from a block.

        Different block types store content differently:
        - html blocks: the content is in fields.data
        - problem blocks: also in fields.data (quiz questions)
        - video blocks: we try to get the transcript, otherwise just metadata
        """
        block_type = block.get("block_type", "")
        def_id = block.get("definition")

        if not def_id or def_id not in definitions:
            return ""

        fields = definitions[def_id].get("fields", {})

        if block_type in ("html", "problem"):
            return clean_html(fields.get("data", ""))

        if block_type == "video":
            # try to get transcript first - it has the actual spoken content
            transcripts = fields.get("transcripts", {})
            if transcripts:
                # prefer English, but take whatever is available
                filename = transcripts.get("en") or next(iter(transcripts.values()), None)
                if filename:
                    text = self._get_transcript(filename)
                    if text:
                        return f"Video transcript: {text}"

            # no transcript available, just note what video it is
            display = fields.get("display_name", "")
            return f"Video: {display}" if display else ""

        return ""

    def _get_display_name(self, block: dict, definitions: dict) -> str:
        """Helper to get display_name from block or definition fields."""
        block_fields = block.get("fields", {})
        def_id = block.get("definition")
        def_fields = definitions.get(def_id, {}).get("fields", {}) if def_id else {}

        return (
            block_fields.get("display_name") or
            def_fields.get("display_name") or
            "Untitled"
        )

    def extract_course(self, course_id: str) -> list[Document]:
        """
        Extract all content from a course and return LlamaIndex Documents.

        We traverse the course tree to track hierarchy - so each section knows
        its parent module, and each content block knows its module and section.
        """
        print(f"\nExtracting: {course_id}")
        documents = []

        structure = self._get_published_structure(course_id)
        if not structure:
            return documents

        # get all the blocks and build a lookup map by block_id
        blocks = structure.get("blocks", {})

        # in Split Mongo, blocks is a dict keyed by block_id
        # each block has "fields" with "children" listing child block_ids
        if isinstance(blocks, list):
            # handle older list format just in case
            blocks = {b.get("block_id"): b for b in blocks}

        # collect all definition IDs so we can fetch them in one query
        def_ids = [b["definition"] for b in blocks.values() if "definition" in b]

        print(f"   Fetching {len(def_ids)} definitions...")
        definitions = {}
        for doc in self.definitions.find({"_id": {"$in": def_ids}}):
            definitions[doc["_id"]] = doc

        # find the course root block to start traversal
        root_block = None
        for block_id, block in blocks.items():
            if block.get("block_type") == "course":
                root_block = block
                break

        if not root_block:
            print("   Could not find course root block")
            return documents

        # traverse the tree: course -> chapters -> sequentials -> verticals -> content
        # we track the current module and section as we go down
        chapters = root_block.get("fields", {}).get("children", [])

        for chapter_id in chapters:
            chapter = blocks.get(chapter_id)
            if not chapter or chapter.get("block_type") != "chapter":
                continue

            module_name = self._get_display_name(chapter, definitions)

            # create a document for the module itself
            if module_name and module_name != "Untitled":
                doc = Document(
                    text=f"Module: {module_name}",
                    metadata={
                        "course_id": course_id,
                        "block_type": "chapter",
                        "display_name": module_name,
                        "module": module_name,
                        "source": f"{course_id}/chapter/{module_name}",
                    }
                )
                documents.append(doc)

            # now get the sections (sequentials) within this chapter
            sequentials = chapter.get("fields", {}).get("children", [])

            for seq_id in sequentials:
                sequential = blocks.get(seq_id)
                if not sequential or sequential.get("block_type") != "sequential":
                    continue

                section_name = self._get_display_name(sequential, definitions)

                # create a document for the section, including its parent module
                if section_name and section_name != "Untitled":
                    content = f"Section: {section_name} (in {module_name})"
                    doc = Document(
                        text=content,
                        metadata={
                            "course_id": course_id,
                            "block_type": "sequential",
                            "display_name": section_name,
                            "module": module_name,
                            "section": section_name,
                            "source": f"{course_id}/sequential/{section_name}",
                        }
                    )
                    documents.append(doc)

                # get the verticals (units) within this section
                verticals = sequential.get("fields", {}).get("children", [])

                for vert_id in verticals:
                    vertical = blocks.get(vert_id)
                    if not vertical or vertical.get("block_type") != "vertical":
                        continue

                    # get the content blocks within this vertical
                    content_blocks = vertical.get("fields", {}).get("children", [])

                    for content_id in content_blocks:
                        content_block = blocks.get(content_id)
                        if not content_block:
                            continue

                        block_type = content_block.get("block_type", "")

                        # skip structural blocks
                        if block_type in ["course", "chapter", "sequential", "vertical"]:
                            continue

                        content = self._extract_content(content_block, definitions)
                        display_name = self._get_display_name(content_block, definitions)

                        # only keep blocks with substantial content
                        if content and len(content) > 50:
                            doc = Document(
                                text=content,
                                metadata={
                                    "course_id": course_id,
                                    "block_type": block_type,
                                    "display_name": display_name,
                                    "module": module_name,
                                    "section": section_name,
                                    "source": f"{course_id}/{block_type}/{display_name}",
                                }
                            )
                            documents.append(doc)

        print(f"   Extracted {len(documents)} content blocks")
        return documents

    def close(self):
        self.client.close()


def index_to_qdrant(documents: list[Document]):
    """
    Take the extracted documents and index them into Qdrant.

    LlamaIndex handles the heavy lifting here:
    1. Chunks the text into smaller pieces
    2. Generates embeddings using FastEmbed (runs locally, no API needed)
    3. Stores everything in Qdrant
    """
    print("\n" + "="*50)
    print("Indexing to Qdrant")
    print("="*50)

    # connect to Qdrant (running in Docker alongside Open edX)
    client = QdrantClient(url=qdrant_config.url)

    # set up the vector store
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=qdrant_config.collection_name
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # we use FastEmbed because it runs locally - no API keys needed
    # bge-small is a good balance of speed and quality
    print("Loading embedding model (bge-small-en)...")
    Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # this is where the magic happens - LlamaIndex chunks, embeds, and stores
    print(f"Processing {len(documents)} documents...")
    VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )

    print("Done! Documents are now in Qdrant.")


def main():
    """
    Main entry point - extract all courses and index them.
    """
    # try to connect to MongoDB
    try:
        extractor = OpenEdXExtractor()
    except Exception as e:
        print(f"Could not connect to MongoDB: {e}")
        print("Make sure Open edX is running (tutor local start)")
        return

    try:
        # get all courses and extract content from each
        courses = extractor.get_courses()
        all_documents = []

        for course in courses:
            docs = extractor.extract_course(course["course_id"])
            all_documents.extend(docs)

        if not all_documents:
            print("No content found to index.")
            return

        print(f"\nTotal documents extracted: {len(all_documents)}")

        # now index everything to Qdrant
        index_to_qdrant(all_documents)

    finally:
        extractor.close()


if __name__ == "__main__":
    main()
