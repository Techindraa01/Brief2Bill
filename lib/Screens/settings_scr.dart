import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:printing/printing.dart';
import 'package:pdf/widgets.dart' as pw;

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
      appBar: AppBar(title: const Text('Company defaults')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            TextField(
              controller: _name,
              decoration: const InputDecoration(labelText: 'Company name'),
            ),
            TextField(
              controller: _address,
              decoration: const InputDecoration(labelText: 'Address'),
            ),
            TextField(
              controller: _upi,
              decoration: const InputDecoration(labelText: 'UPI ID'),
            ),
            const SizedBox(height: 20),
            ElevatedButton(onPressed: _save, child: const Text('Save')),
          ],
        ),
      ),
    );
  }
}