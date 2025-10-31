import 'package:flutter/material.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:pdf/pdf.dart';

class PDFGenerator {
  static Future<pw.Document> buildPdf(Map bundle) async {
    final pdf = pw.Document();
    final seller = Map.of(bundle['seller'] ?? {});
    final buyer = Map.of(bundle['buyer'] ?? {});
    final items = (bundle['items'] as List).cast<Map>();
    final totals = Map.of(bundle['totals'] ?? {});

    final theme = pw.ThemeData.withFont(base: await PdfGoogleFonts.openSansRegular());

    pdf.addPage(pw.MultiPage(
        theme: theme,
        pageFormat: PdfPageFormat.a4,
        build: (pw.Context ctx) {
          return [
            pw.Row(mainAxisAlignment: pw.MainAxisAlignment.spaceBetween, children: [
              pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [pw.Text(seller['name'] ?? '', style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold)), pw.Text(seller['address'] ?? '')]),
              pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.end, children: [pw.Text(bundle['doc_meta']?['doc_no'] ?? ''), pw.Text('Issue: ${bundle['dates']?['issue_date'] ?? ''}')])
            ]),
            pw.SizedBox(height: 10),
            pw.Text('Buyer', style: pw.TextStyle(fontWeight: pw.FontWeight.bold)),
            pw.Text(buyer['name'] ?? ''),
            pw.SizedBox(height: 12),
            pw.Table.fromTextArray(
                headers: ['Description','Qty','Unit','Unit Price','Tax%','Line'],
                data: items.map((it){
                  final qty = it['qty'] ?? 1;
                  final unit = it['unit'] ?? '';
                  final up = it['unit_price'] ?? 0;
                  final tax = it['tax_rate'] ?? 0;
                  final line = (qty * up) + ((qty*up) * (tax/100));
                  return [it['description'] ?? '', qty.toString(), unit, up.toString(), tax.toString(), line.toStringAsFixed(2)];
                }).toList()
            ),
            pw.Divider(),
            pw.Container(alignment: pw.Alignment.centerRight, child: pw.Column(children: [
              pw.Row(mainAxisAlignment: pw.MainAxisAlignment.end, children: [pw.Text('Subtotal: '), pw.Text(totals['subtotal']?.toString() ?? '0')]),
              pw.Row(mainAxisAlignment: pw.MainAxisAlignment.end, children: [pw.Text('Tax Total: '), pw.Text(totals['tax_total']?.toString() ?? '0')]),
              pw.SizedBox(height:4), pw.Row(mainAxisAlignment: pw.MainAxisAlignment.end, children: [pw.Text('Grand Total: ', style: pw.TextStyle(fontWeight: pw.FontWeight.bold)), pw.Text(totals['grand_total']?.toString() ?? '0', style: pw.TextStyle(fontWeight: pw.FontWeight.bold))])
            ])),
            pw.SizedBox(height: 12),
            pw.Text('Terms', style: pw.TextStyle(fontWeight: pw.FontWeight.bold)),
            if(bundle['terms']?['bullets'] != null) pw.Column(children: (bundle['terms']['bullets'] as List).map((b)=>pw.Bullet(text: b)).toList()),
            pw.SizedBox(height: 12),
            pw.Text('Notes'),
            pw.Text(bundle['notes'] ?? ''),
            pw.SizedBox(height: 20),
            pw.Row(mainAxisAlignment: pw.MainAxisAlignment.spaceBetween, children: [
              pw.Text('Payment: ${bundle['payment']?['mode'] ?? ''}'),
              if(bundle['payment']?['upi_deeplink'] != null) pw.BarcodeWidget(data: bundle['payment']['upi_deeplink'], barcode: pw.Barcode.qrCode())
            ])
          ];
        }
    ));
    return pdf;
  }
}