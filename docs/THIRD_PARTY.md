# Third-party components

This repository's code and synthetic dataset definitions are MIT licensed. Installed dependencies and models retain their own licenses; they are not relicensed by this project.

- [RapidOCR 1.4.4](https://github.com/RapidAI/RapidOCR/tree/v1.4.4/python/rapidocr_onnxruntime): package metadata declares Apache-2.0; ships PP-OCR detection/recognition and angle classification ONNX artifacts. Refer to upstream for model provenance and licensing.
- [ONNX Runtime](https://github.com/microsoft/onnxruntime): CPU inference.
- [pdfplumber](https://github.com/jsvine/pdfplumber) and PDFMiner: reference text extraction.
- [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) / PDFium: rasterization; bundled third-party notices apply.
- [ReportLab](https://www.reportlab.com/): deterministic synthetic PDF generation.
- [Streamlit](https://docs.streamlit.io/): local review interface.
- Pillow, NumPy and OpenCV are image-processing dependencies; pytest supplies test execution.

Exact installed versions are in requirements-lock.txt. Model artifact fingerprints from the measured environment are in model-fingerprints.json. No OCR model binaries are committed.
