import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:printing/printing.dart';
import 'package:pdf/widgets.dart' as pw;

import '../Utils/reusables.dart';

class SellerSettings extends StatefulWidget { const SellerSettings({super.key}); @override State<SellerSettings> createState() => _SellerSettingsState(); }
class _SellerSettingsState extends State<SellerSettings> {
  final _box = Hive.box('settings');
  final _name = TextEditingController();
  final _address = TextEditingController();
  final _upi = TextEditingController();

  @override
  void initState() {
    super.initState();
    final s = _box.get('seller', defaultValue: {});
    _name.text = s['name'] ?? '';
    _address.text = s['address'] ?? '';
    _upi.text = _box.get('upi', defaultValue: 'acme@upi');
  }

  @override
  void dispose() {
    _name.dispose();
    _address.dispose();
    _upi.dispose();
    super.dispose();
  }

  void _save() {
    _box.put('seller', {'name': _name.text, 'address': _address.text});
    _box.put('upi', _upi.text);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Saved')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(title: const Text('Company Defaults', style: TextStyle(color: Colors.white, fontFamily: 'Roboto', fontSize: 16, fontWeight: FontWeight.w600)
      ),
        flexibleSpace: Container(
          decoration:  BoxDecoration(
            gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: <Color>[Colors.blue.shade800, Colors.blue.shade900]),
          ),
        ),
        centerTitle: true,
        iconTheme: IconThemeData(color: Colors.white),
      ),
      body: Padding(
        padding: const EdgeInsets.all(10),
        child: SingleChildScrollView(
          child: Column(
            children: [
              Container(
                decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10)
                ),
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Column(
                    children: [
                      CustTextFields( title: 'COMPANY NAME', textEditingController: _name,),

                      Divider(color: Colors.grey.shade300,thickness: 1,),
                      CustTextFields( title: 'ADDRESS', textEditingController: _address,),
                      Divider(color: Colors.grey.shade300,thickness: 1,),
                      CustTextFields( title: 'UPI ID', textEditingController: _upi,),



                    ],
                  ),
                ),
              ),

              const SizedBox(height: 30),
              CustButtons(text: "Save", onpressed: _save, boxcolor: Colors.blue.shade600,)
            ],
          ),
        ),
      ),
    );
  }
}