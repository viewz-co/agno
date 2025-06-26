# Textract Dependency Removal and Replacement

## Overview

This document outlines the removal of the problematic `textract` dependency from the Agno codebase and its replacement with a modern, reliable document processing solution.

## Problem Statement

The `textract` library has been causing CI/CD failures due to:

1. **Broken Dependencies**: Version 1.6.5 has invalid metadata with `extract-msg (<=0.29.*)`
2. **Build Failures**: The `.*` suffix can only be used with `==` or `!=` operators  
3. **Maintenance Issues**: The library is poorly maintained and has unresolved dependency conflicts

## Solution: UniversalDocumentReader

We've replaced `textract` with a new `UniversalDocumentReader` class that provides:

- **Modern Dependencies**: Uses well-maintained libraries like `pypdf`, `python-docx`
- **Graceful Fallbacks**: Multiple extraction strategies with fallback mechanisms
- **Better Error Handling**: Robust error handling and logging
- **Type Safety**: Full type annotations and better IDE support
- **Extensibility**: Easy to add new document format support

## Migration Details

### Files Modified

1. **New Implementation**: `libs/agno/agno/document/reader/universal_reader.py`
2. **S3 Text Reader**: `libs/agno/agno/document/reader/s3/text_reader.py`
3. **LightRAG Knowledge Base**: `libs/agno/agno/knowledge/light_rag.py`
4. **Dependencies**: `libs/agno/pyproject.toml`
5. **Tests**: `libs/agno/tests/test_universal_reader.py`

### Key Changes

#### 1. UniversalDocumentReader Features

- **PDF Support**: Both `pypdf` and `PyMuPDF` (fitz) backends
- **DOCX Support**: Native `python-docx` integration
- **Text Files**: UTF-8 with error handling
- **RTF Support**: Basic RTF parsing with optional `striprtf` enhancement
- **OCR Support**: `pytesseract` for scanned documents and images
- **Fallback Reader**: For unknown file types

#### 2. Dependency Detection

The reader automatically detects available dependencies and adapts:

```python
def _check_dependencies(self):
    """Check if required dependencies are available"""
    self.available_readers = {}
    
    try:
        import pypdf
        self.available_readers['pdf'] = 'pypdf'
    except ImportError:
        try:
            import fitz
            self.available_readers['pdf'] = 'fitz'
        except ImportError:
            logger.warning("No PDF reader available")
```

#### 3. Error Handling Strategy

- **Graceful Degradation**: If one method fails, try alternatives
- **Detailed Logging**: Clear error messages for debugging
- **Empty Results**: Return empty list instead of crashing
- **Resource Cleanup**: Proper file handle management

### Dependencies Update

#### Removed
- `textract` (completely removed from all dependency lists)

#### Added
```toml
universal = ["pypdf", "python-docx", "pytesseract", "Pillow", "striprtf"]
```

#### Optional Dependencies

Users can install specific document processing capabilities:

```bash
# Basic installation (text files only)
pip install agno

# PDF support
pip install agno[pdf]

# DOCX support  
pip install agno[docx]

# Full document processing
pip install agno[universal]

# OCR support for scanned documents
pip install pytesseract Pillow
```

## Migration Guide for Users

### For Library Users

The API remains unchanged. Existing code using `S3TextReader` or `LightRagKnowledgeBase` will continue working without modifications.

### For Docker Users

Replace this problematic line in your Dockerfile:

```dockerfile
# OLD - This will fail
RUN pip install --no-deps textract
```

With this modern approach:

```dockerfile
# NEW - This works reliably
RUN pip install pypdf python-docx
# Optional: Add OCR support
RUN pip install pytesseract Pillow
```

### For Development

1. **Install Dependencies**:
   ```bash
   pip install agno[universal]
   ```

2. **Run Tests**:
   ```bash
   pytest libs/agno/tests/test_universal_reader.py
   ```

3. **Use the Reader**:
   ```python
   from agno.document.reader.universal_reader import UniversalDocumentReader
   
   reader = UniversalDocumentReader()
   documents = reader.read("document.pdf")
   ```

## Performance Comparison

| Library | Format Support | Dependency Issues | Maintenance | Performance |
|---------|---------------|-------------------|-------------|-------------|
| textract | Excellent | ❌ Broken | ❌ Poor | Good |
| UniversalDocumentReader | Good | ✅ Clean | ✅ Active | Good |

## Benefits of Migration

### 1. **Reliability**
- ✅ No more CI/CD failures due to broken dependencies
- ✅ Well-maintained, actively developed libraries
- ✅ Better error handling and recovery

### 2. **Performance** 
- ✅ Faster startup (no heavy dependency loading)
- ✅ Memory efficient (load only needed libraries)
- ✅ Streaming support for large files

### 3. **Maintainability**
- ✅ Clean, readable code with type annotations
- ✅ Comprehensive test coverage
- ✅ Modular design for easy extension

### 4. **Developer Experience**
- ✅ Better IDE support with type hints
- ✅ Clear error messages and logging
- ✅ Flexible dependency installation

## Implementation Strategy

### Phase 1: Core Replacement ✅
- [x] Create `UniversalDocumentReader`
- [x] Update `S3TextReader` 
- [x] Update `LightRagKnowledgeBase`
- [x] Remove `textract` from dependencies

### Phase 2: Testing & Validation ✅
- [x] Comprehensive unit tests
- [x] Integration tests with existing workflows
- [x] Performance benchmarking

### Phase 3: Documentation & Migration 📝
- [x] Migration documentation
- [ ] Update README files
- [ ] Update installation instructions
- [ ] Communicate changes to users

## Backward Compatibility

The changes maintain 100% backward compatibility:

- ✅ Same API surface
- ✅ Same return types
- ✅ Same error handling patterns
- ✅ Same configuration options

## Future Enhancements

### Planned Features
1. **Enhanced OCR**: Better preprocessing for scanned documents
2. **Table Extraction**: Structured table parsing from PDFs
3. **Metadata Extraction**: Document properties and embedded metadata
4. **Performance Optimization**: Parallel processing for large documents
5. **Cloud Integration**: AWS Textract, Google Document AI as optional backends

### Extensibility Points

The `UniversalDocumentReader` is designed for easy extension:

```python
class EnhancedDocumentReader(UniversalDocumentReader):
    def _read_csv(self, file_path: Path) -> List[Document]:
        """Custom CSV reader implementation"""
        # Implementation here
        pass
    
    def read(self, file_path: Union[str, Path]) -> List[Document]:
        file_path = Path(file_path)
        if file_path.suffix.lower() == '.csv':
            return self._read_csv(file_path)
        return super().read(file_path)
```

## Conclusion

The migration from `textract` to `UniversalDocumentReader` represents a significant improvement in:

- **Reliability**: No more broken dependencies
- **Maintainability**: Clean, modern codebase
- **Performance**: Efficient resource usage
- **Developer Experience**: Better tooling and documentation

This change ensures Agno's document processing capabilities remain robust and future-proof while eliminating the CI/CD failures that have been impacting development workflows.

## Support

For questions or issues related to this migration:

1. **Documentation**: Check this migration guide
2. **Tests**: Run the comprehensive test suite
3. **Issues**: Create GitHub issues for any problems
4. **Community**: Ask questions in Discord/discussions

The migration maintains full backward compatibility while providing a more reliable foundation for document processing in Agno. 