#!/usr/bin/env python3
"""
PDF Processor for Ruppert's Book
--------------------------------
Extracts content from Ruppert's "Statistics and Data Analysis for Financial Engineering" book,
chunks it appropriately, and prepares it for ingestion into Weaviate.
"""

import os
import re
import json
import argparse
import subprocess
from pathlib import Path
import nltk
from nltk.tokenize import sent_tokenize

# Download NLTK data
nltk.download('punkt', quiet=True)

class PDFProcessor:
    def __init__(self, pdf_path, output_dir):
        """Initialize the PDF processor with paths."""
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.ensure_output_dir()
        
    def ensure_output_dir(self):
        """Ensure the output directory exists."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_text_with_pdftotext(self):
        """Extract text from PDF using pdftotext (from poppler-utils)."""
        output_file = os.path.join(self.output_dir, "raw_text.txt")
        
        # Run pdftotext with layout preservation
        subprocess.run([
            "pdftotext",
            "-layout",  # Maintain layout
            self.pdf_path,
            output_file
        ], check=True)
        
        print(f"Extracted raw text to {output_file}")
        return output_file
    
    def extract_text_with_pdftohtml(self):
        """Extract text and structure using pdftohtml (from poppler-utils)."""
        output_file = os.path.join(self.output_dir, "content.html")
        
        # Run pdftohtml with options to extract structure
        subprocess.run([
            "pdftohtml",
            "-s",  # Generate single HTML file
            "-i",  # Ignore images
            "-noframes",  # Don't generate frames
            self.pdf_path,
            os.path.join(self.output_dir, "content")
        ], check=True)
        
        print(f"Extracted HTML content to {output_file}")
        return output_file
    
    def extract_metadata(self):
        """Extract metadata using pdfinfo (from poppler-utils)."""
        result = subprocess.run([
            "pdfinfo",
            self.pdf_path
        ], capture_output=True, text=True, check=True)
        
        metadata = {}
        for line in result.stdout.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
        
        metadata_file = os.path.join(self.output_dir, "metadata.json")
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Extracted metadata to {metadata_file}")
        return metadata
    
    def identify_chapters_and_sections(self, text_file):
        """Identify chapters and sections in the extracted text."""
        with open(text_file, "r") as f:
            content = f.read()
        
        # Regular expressions for chapter and section detection
        chapter_pattern = re.compile(r'Chapter\s+(\d+)[.\s]+([^\n]+)', re.IGNORECASE)
        section_pattern = re.compile(r'(\d+\.\d+)[.\s]+([^\n]+)')
        
        # Find chapters
        chapters = []
        for match in chapter_pattern.finditer(content):
            chapter_num = match.group(1)
            chapter_title = match.group(2).strip()
            start_pos = match.start()
            chapters.append({
                "number": chapter_num,
                "title": chapter_title,
                "start_position": start_pos
            })
        
        # Sort chapters by position
        chapters.sort(key=lambda x: x["start_position"])
        
        # Find end positions
        for i in range(len(chapters) - 1):
            chapters[i]["end_position"] = chapters[i + 1]["start_position"]
        
        # Last chapter ends at the end of the document
        if chapters:
            chapters[-1]["end_position"] = len(content)
        
        # Extract sections within chapters
        for chapter in chapters:
            chapter_content = content[chapter["start_position"]:chapter["end_position"]]
            sections = []
            
            for match in section_pattern.finditer(chapter_content):
                section_num = match.group(1)
                section_title = match.group(2).strip()
                start_pos = match.start() + chapter["start_position"]
                sections.append({
                    "number": section_num,
                    "title": section_title,
                    "start_position": start_pos
                })
            
            # Sort sections by position
            sections.sort(key=lambda x: x["start_position"])
            
            # Find end positions for sections
            for i in range(len(sections) - 1):
                sections[i]["end_position"] = sections[i + 1]["start_position"]
            
            # Last section ends at the end of the chapter
            if sections:
                sections[-1]["end_position"] = chapter["end_position"]
            
            chapter["sections"] = sections
        
        # Save structure to file
        structure_file = os.path.join(self.output_dir, "structure.json")
        with open(structure_file, "w") as f:
            json.dump(chapters, f, indent=2)
        
        print(f"Extracted structure to {structure_file}")
        return chapters
    
    def detect_code_blocks(self, text):
        """Detect code blocks in text."""
        # Patterns for R and Python code
        r_pattern = re.compile(r'```r\s*(.*?)\s*```|> (.*?)(\n\n|\Z)', re.DOTALL)
        python_pattern = re.compile(r'```python\s*(.*?)\s*```|>>> (.*?)(\n\n|\Z)', re.DOTALL)
        
        code_blocks = []
        
        # Find R code blocks
        for match in r_pattern.finditer(text):
            code = match.group(1) or match.group(2)
            if code:
                code_blocks.append({
                    "language": "r",
                    "code": code.strip(),
                    "start": match.start(),
                    "end": match.end()
                })
        
        # Find Python code blocks
        for match in python_pattern.finditer(text):
            code = match.group(1) or match.group(2)
            if code:
                code_blocks.append({
                    "language": "python",
                    "code": code.strip(),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return code_blocks
    
    def chunk_content(self, chapters, text_file):
        """Chunk content based on chapters and sections."""
        with open(text_file, "r") as f:
            content = f.read()
        
        chunks = []
        
        for chapter in chapters:
            chapter_content = content[chapter["start_position"]:chapter["end_position"]]
            
            # If chapter has sections, chunk by section
            if chapter["sections"]:
                for section in chapter["sections"]:
                    section_start = section["start_position"] - chapter["start_position"]
                    section_end = section["end_position"] - chapter["start_position"]
                    section_content = chapter_content[section_start:section_end]
                    
                    # Detect code blocks
                    code_blocks = self.detect_code_blocks(section_content)
                    
                    # Create chunk
                    chunk = {
                        "content": section_content,
                        "metadata": {
                            "chapter_number": chapter["number"],
                            "chapter_title": chapter["title"],
                            "section_number": section["number"],
                            "section_title": section["title"],
                            "has_code": len(code_blocks) > 0
                        },
                        "code_blocks": code_blocks
                    }
                    chunks.append(chunk)
            else:
                # If no sections, chunk the chapter into smaller pieces
                # Use simple paragraph splitting instead of sentence tokenization
                paragraphs = re.split(r'\n\s*\n', chapter_content)
                
                # Group paragraphs into chunks of approximately 1000 characters
                current_chunk = ""
                for paragraph in paragraphs:
                    if len(current_chunk) + len(paragraph) < 1000:
                        current_chunk += paragraph + "\n\n"
                    else:
                        # Detect code blocks
                        code_blocks = self.detect_code_blocks(current_chunk)
                        
                        # Create chunk
                        chunk = {
                            "content": current_chunk.strip(),
                            "metadata": {
                                "chapter_number": chapter["number"],
                                "chapter_title": chapter["title"],
                                "has_code": len(code_blocks) > 0
                            },
                            "code_blocks": code_blocks
                        }
                        chunks.append(chunk)
                        current_chunk = paragraph + "\n\n"
                
                # Add the last chunk if not empty
                if current_chunk.strip():
                    code_blocks = self.detect_code_blocks(current_chunk)
                    chunk = {
                        "content": current_chunk.strip(),
                        "metadata": {
                            "chapter_number": chapter["number"],
                            "chapter_title": chapter["title"],
                            "has_code": len(code_blocks) > 0
                        },
                        "code_blocks": code_blocks
                    }
                    chunks.append(chunk)
        
        # Save chunks to file
        chunks_file = os.path.join(self.output_dir, "chunks.json")
        with open(chunks_file, "w") as f:
            json.dump(chunks, f, indent=2)
        
        print(f"Created {len(chunks)} chunks and saved to {chunks_file}")
        return chunks
    
    def process(self):
        """Process the PDF and extract all necessary information."""
        # Extract text and metadata
        text_file = self.extract_text_with_pdftotext()
        html_file = self.extract_text_with_pdftohtml()
        metadata = self.extract_metadata()
        
        # Identify structure
        chapters = self.identify_chapters_and_sections(text_file)
        
        # Chunk content
        chunks = self.chunk_content(chapters, text_file)
        
        return {
            "text_file": text_file,
            "html_file": html_file,
            "metadata": metadata,
            "chapters": chapters,
            "chunks": chunks
        }

def main():
    parser = argparse.ArgumentParser(description="Process Ruppert's book PDF for RAG ingestion")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--output-dir", default="output", help="Output directory for processed files")
    
    args = parser.parse_args()
    
    processor = PDFProcessor(args.pdf_path, args.output_dir)
    result = processor.process()
    
    print(f"Processing complete. {len(result['chunks'])} chunks created.")

if __name__ == "__main__":
    main()
