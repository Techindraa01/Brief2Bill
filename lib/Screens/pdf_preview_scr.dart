import 'package:flutter/material.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

class PdfPreviewScreen extends StatelessWidget {
  final pw.Document document;
  final Map bundle;
  const PdfPreviewScreen({super.key, required this.document, required this.bundle});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Preview')),
      body: PdfPreview(
        build: (format) => document.save(),
        allowPrinting: true,
        actions: [
          PdfPreviewAction(
            icon: const Icon(Icons.share),
            onPressed: (context, build, pageFormat) async {
              final bytes = await document.save();
              await Printing.sharePdf(
                bytes: bytes,
                filename:
                '${bundle['doc_meta']?['doc_no'] ?? 'document'}.pdf',
              );
            },
          ),
        ],
      ),
    );
  }
}
