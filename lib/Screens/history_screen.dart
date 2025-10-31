import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:invoicepdf/Screens/pdf_preview_scr.dart';
import 'package:pdf/widgets.dart' as pw;

class HistoryScreen extends StatelessWidget { const HistoryScreen({super.key});
@override Widget build(BuildContext context){ final box = Hive.box('history'); final items = box.values.toList().reversed.toList(); return Scaffold(appBar: AppBar(title: const Text('History')), body: ListView.builder(itemCount: items.length, itemBuilder: (_,i){ final it = items[i]; final bundle = Map.of(it['bundle']); return ListTile(title: Text(bundle['doc_meta']?['doc_no'] ?? 'Document'), subtitle: Text(it['created'] ?? ''), onTap: ()=>Navigator.of(context).push(MaterialPageRoute(builder: (_)=>PdfPreviewScreen(document: pw.Document() /* placeholder */, bundle: bundle)))); })); }
}