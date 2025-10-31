import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:invoicepdf/Screens/pdf_gen_screen.dart';
import 'package:invoicepdf/Screens/pdf_preview_scr.dart';

class EditorScreen extends StatefulWidget {
  final Map initialBundle;
  const EditorScreen({super.key, required this.initialBundle});
  @override
  State<EditorScreen> createState() => _EditorScreenState();
}
class _EditorScreenState extends State<EditorScreen> {
  late Map bundle;
  final _controllers = <String, TextEditingController>{};

  @override
  void initState(){
    super.initState();
    bundle = jsonDecode(jsonEncode(widget.initialBundle));
    _initControllers();
  }
  void _initControllers(){
    _controllers['notes'] = TextEditingController(text: bundle['notes'] ?? '');
    _controllers['buyer_name'] = TextEditingController(text: bundle['buyer']?['name'] ?? '');
    _controllers['buyer_email'] = TextEditingController(text: bundle['buyer']?['email'] ?? '');
  }
  @override
  void dispose(){
    for(final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  void _recalculateTotals(){
    final items = (bundle['items'] as List).cast<Map>();
    num subtotal = 0;
    num taxTotal = 0;
    for(final it in items){
      final qty = (it['qty'] ?? 1) as num;
      final price = (it['unit_price'] ?? 0) as num;
      final tax = (it['tax_rate'] ?? 0) as num;
      final line = qty * price;
      subtotal += line;
      taxTotal += (line * tax / 100);
    }
    bundle['totals'] = {'subtotal': subtotal, 'tax_total': taxTotal, 'grand_total': subtotal + taxTotal};
    setState((){});
  }

  void _addItem(){
    (bundle['items'] as List).add({'description':'New item','qty':1,'unit':'pcs','unit_price':0,'tax_rate':0});
    _recalculateTotals();
  }

  void _removeItem(int idx){
    (bundle['items'] as List).removeAt(idx);
    _recalculateTotals();
  }

  Future<void> _previewPdf() async {
    final pdf = await PDFGenerator.buildPdf(bundle);
    // Save into history
    await Hive.box('history').add({'bundle':bundle,'created':DateTime.now().toIso8601String()});
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => PdfPreviewScreen(document: pdf, bundle: bundle)));
  }

  @override
  Widget build(BuildContext context){
    final items = (bundle['items'] as List).cast<Map>();
    return Scaffold(
        appBar: AppBar(title: const Text('Editor'), actions: [TextButton(onPressed: _recalculateTotals, child: const Text('Recalculate')), TextButton(onPressed: _previewPdf, child: const Text('Preview PDF'))]),
        body: Padding(
            padding: const EdgeInsets.all(12.0),
            child: ListView(children: [
              ExpansionTile(title: const Text('Seller'), children: [ListTile(title: Text(bundle['seller']?['name'] ?? ''))]),
              ExpansionTile(title: const Text('Buyer'), children: [
                Padding(padding: const EdgeInsets.all(8.0), child: TextField(controller: _controllers['buyer_name'], decoration: const InputDecoration(labelText: 'Buyer name'))),
                Padding(padding: const EdgeInsets.all(8.0), child: TextField(controller: _controllers['buyer_email'], decoration: const InputDecoration(labelText: 'Buyer email'))),
                Padding(padding: const EdgeInsets.all(8.0), child: ElevatedButton(onPressed: (){bundle['buyer']={'name':_controllers['buyer_name']!.text,'email':_controllers['buyer_email']!.text}; setState(()=>{});}, child: const Text('Apply')))
              ]),
              ExpansionTile(title: const Text('Items'), children: [
                ListView.separated(
                    separatorBuilder: (_,__)=>const Divider(),
                    itemCount: items.length,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemBuilder: (context, i){
                      final it = Map.of(items[i]);
                      final desc = TextEditingController(text: it['description']);
                      final qty = TextEditingController(text: it['qty'].toString());
                      final price = TextEditingController(text: it['unit_price'].toString());
                      final tax = TextEditingController(text: it['tax_rate'].toString());
                      return Padding(
                          padding: const EdgeInsets.all(8.0),
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            TextField(controller: desc, decoration: const InputDecoration(labelText: 'Description'), onChanged: (v)=>it['description']=v),
                            Row(children: [Expanded(child: TextField(controller: qty, decoration: const InputDecoration(labelText: 'Qty'), keyboardType: TextInputType.number, onChanged: (v)=>it['qty']=num.tryParse(v) ?? 1)), const SizedBox(width:8), Expanded(child: TextField(controller: price, decoration: const InputDecoration(labelText: 'Unit price'), keyboardType: TextInputType.number, onChanged: (v)=>it['unit_price']=num.tryParse(v) ?? 0)), const SizedBox(width:8), Expanded(child: TextField(controller: tax, decoration: const InputDecoration(labelText: 'Tax %'), keyboardType: TextInputType.number, onChanged: (v)=>it['tax_rate']=num.tryParse(v) ?? 0))]),
                            Row(children: [TextButton(onPressed: ()=>setState(()=>_removeItem(i)), child: const Text('Remove')), const Spacer(), IconButton(onPressed: ()=>setState(()=> items.insert(i, Map.of(items[i]))), icon: const Icon(Icons.copy))])
                          ])
                      );
                    }
                ),
                Padding(padding: const EdgeInsets.all(8.0), child: ElevatedButton(onPressed: _addItem, child: const Text('Add Item')))
              ]),
              ExpansionTile(title: const Text('Terms'), children: [Padding(padding: const EdgeInsets.all(8.0), child: Text(bundle['terms']?['title'] ?? ''))]),
              ExpansionTile(title: const Text('Payment'), children: [Padding(padding: const EdgeInsets.all(8.0), child: Text('UPI: ${bundle['payment']?['upi_id'] ?? ''}')), Padding(padding: const EdgeInsets.all(8.0), child: ElevatedButton(onPressed: ()=>_generatePayLink(), child: const Text('Generate Pay Link')))]),
              ExpansionTile(title: const Text('Dates & Meta'), children: [Padding(padding: const EdgeInsets.all(8.0), child: Text('Issue: ${bundle['dates']?['issue_date'] ?? ''}'))]),
              Padding(padding: const EdgeInsets.all(8.0), child: TextField(controller: _controllers['notes'], maxLines: 3, decoration: const InputDecoration(labelText: 'Notes'))),
              Padding(padding: const EdgeInsets.symmetric(vertical:12.0), child: Row(children: [ElevatedButton(onPressed: (){bundle['notes']=_controllers['notes']!.text; _recalculateTotals();}, child: const Text('Apply Changes')), const SizedBox(width:12), OutlinedButton(onPressed: ()=>_resetToAIDraft(), child: const Text('Reset to AI Draft'))]))
            ])
        )
    );
  }

  void _resetToAIDraft(){
    bundle = jsonDecode(jsonEncode(widget.initialBundle));
    _initControllers();
    _recalculateTotals();
  }

  void _generatePayLink(){
    final upi = bundle['payment']?['upi_id'] ?? Hive.box('settings').get('upi',defaultValue: 'acme@upi');
    final amount = bundle['totals']?['grand_total'] ?? 0;
    final meta = bundle['doc_meta']?['doc_no'] ?? 'DOC';
    final deeplink = 'upi://pay?pa=\$upi&pn=${Uri.encodeComponent(bundle['seller']?['name'] ?? '')}&am=\$amount&cu=INR&tn=Advance%2050%25&tr=\$meta';
    bundle['payment'] = {...(bundle['payment'] ?? {}), 'upi_deeplink': deeplink};
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Pay link generated')));
  }
}