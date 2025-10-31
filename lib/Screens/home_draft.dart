import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:intl/intl.dart';
import 'package:invoicepdf/Screens/settings_scr.dart';

import 'client_scr.dart';
import 'editor_screen.dart';
import 'history_screen.dart';

class HomeDraft extends StatefulWidget {
  const HomeDraft({super.key});
  @override
  State<HomeDraft> createState() => _HomeDraftState();
}
class _HomeDraftState extends State<HomeDraft> {
  final TextEditingController _desc = TextEditingController();
  String _selectedDoc = 'Quotation';
  String _currency = 'INR';
  bool _loading = false;

  @override
  void dispose() {
    _desc.dispose();
    super.dispose();
  }

  Future<void> _generateDraft() async {
    setState(() => _loading = true);
    try {
      // Simulate call to /v1/draft returning the draft bundle - here we synthesize from input.
      final now = DateFormat('yyyy-MM-dd').format(DateTime.now());
      final draft = {
        'doc_type': _selectedDoc.toUpperCase(),
        'locale': 'en-IN',
        'currency': _currency,
        'seller': Hive.box('settings').get('seller', defaultValue: {
          'name': 'Acme Solutions',
          'address': '401, Some Park, Surat',
          'email': 'billing@acme.in'
        }),
        'buyer': {'name': 'Client Name', 'email': 'client@example.com'},
        'doc_meta': {'doc_no': 'D-${DateTime.now().millisecondsSinceEpoch}', 'ref_no': ''},
        'dates': {'issue_date': now, 'valid_till': DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 15)))},
        'items': [
          {'description': 'E-commerce landing redesign', 'qty': 1, 'unit': 'job', 'unit_price': 28000, 'tax_rate': 18, 'hsn_sac': '998313'},
          {'description': 'Maintenance (3 months)', 'qty': 1, 'unit': 'lot', 'unit_price': 9000, 'tax_rate': 18}
        ],
        'totals': {'subtotal': 37000, 'tax_total': 6660, 'grand_total': 43660},
        'terms': {'title': 'Terms & Conditions', 'bullets': ['Quotation valid 15 days.','50% advance, balance on delivery.']},
        'notes': _desc.text,
        'payment': {'mode': 'UPI', 'upi_id': Hive.box('settings').get('upi', defaultValue: 'acme@upi')}
      };

      final box = Hive.box('drafts');
      await box.add({'status': 'generated', 'bundle': draft, 'created': DateTime.now().toIso8601String()});
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => EditorScreen(initialBundle: draft)));
    } catch (e) {
      // Show inline error
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error generating draft: \$e')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home - Draft')),
      body: Padding(
        padding: const EdgeInsets.all(12.0),
        child: LayoutBuilder(builder: (context, constraints) {
          final isWide = constraints.maxWidth > 700;
          return Column(children: [
            Expanded(
                child: SingleChildScrollView(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const SizedBox(height: 8),
                      TextField(
                        controller: _desc,
                        maxLines: 5,
                        decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Describe the work requirement...'),
                      ),
                      const SizedBox(height: 12),
                      Wrap(spacing: 8, children: ['Quotation','Tax Invoice','Project Brief'].map((t) {
                        final selected = t==_selectedDoc;
                        return ChoiceChip(label: Text(t), selected: selected, onSelected: (_) => setState(()=>_selectedDoc=t));
                      }).toList()),
                      const SizedBox(height: 12),
                      Row(children: [
                        DropdownButton<String>(value: _currency, items: ['INR','USD'].map((c)=>DropdownMenuItem(value:c,child:Text(c))).toList(), onChanged: (v)=>setState(()=>_currency=v!)),
                        const SizedBox(width: 16),
                        TextButton(onPressed: ()=>Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SellerSettings())), child: const Text('Set Seller Details')),
                        const SizedBox(width: 8),
                        TextButton(onPressed: ()=>Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ClientsScreen())), child: const Text('Saved Clients'))
                      ]),
                    ])
                )
            ),
            SizedBox(height: 56, child: Row(children: [
              Expanded(child: ElevatedButton(child: _loading ? const CircularProgressIndicator.adaptive() : const Text('Generate Draft'), onPressed: _loading ? null : _generateDraft)),
              const SizedBox(width: 12),
              OutlinedButton(child: const Text('History'), onPressed: ()=>Navigator.of(context).push(MaterialPageRoute(builder: (_) => const HistoryScreen())))
            ]))
          ]);
        }),
      ),
    );
  }
}
