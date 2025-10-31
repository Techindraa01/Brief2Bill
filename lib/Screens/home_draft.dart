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
  final List<String> _currencies = const ['INR', 'USD', 'EUR', 'GBP', 'AUD', 'CAD'];

  bool get _canGenerate => !_loading && _desc.text.trim().length >= 10;

  @override
  void dispose() {
    _desc.dispose();
    super.dispose();
  }

  Future<void> _generateDraft() async {
    if (!_canGenerate) return;
    setState(() => _loading = true);
    try {
      final now = DateFormat('yyyy-MM-dd').format(DateTime.now());
      final baseSeller = Hive.box('settings').get('seller', defaultValue: {
        'name': 'Acme Solutions Pvt Ltd',
        'address': '401, Some Park, Surat, GJ 395007',
        'email': 'billing@acme.in',
        'phone': '+91-9800000000'
      });
      final seller = {
        ...baseSeller,
        'gstin': baseSeller['gstin'] ?? '24ABCDE1234F1Z5',
        'pan': baseSeller['pan'] ?? 'ABCDE1234F',
        'bank': {
          'account_name': baseSeller['bank']?['account_name'] ?? baseSeller['name'] ?? 'Acme Solutions Pvt Ltd',
          'account_no': baseSeller['bank']?['account_no'] ?? '1234567890123',
          'ifsc': baseSeller['bank']?['ifsc'] ?? 'HDFC0123456',
          'upi_id': Hive.box('settings').get('upi', defaultValue: 'acme@upi')
        }
      };

      Map<String, dynamic> draft = {
        'doc_type': _selectedDoc.toUpperCase(),
        'locale': 'en-IN',
        'currency': _currency,
        'seller': seller,
        'buyer': {
          'name': 'Indigo Retail Pvt Ltd',
          'email': 'ops@indigo.example',
          'phone': '+91-9810000000',
          'address': 'Nariman Point, Mumbai, IN',
          'gstin': '27PQRSX1234A1Z2'
        },
        'doc_meta': {
          'doc_no': 'D-${DateTime.now().millisecondsSinceEpoch}',
          'ref_no': '',
          'po_no': ''
        },
        'dates': {
          'issue_date': now,
          'due_date': DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 7))),
          'valid_till': DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 15)))
        },
        'items': [
          {
            'description': 'E-commerce landing redesign',
            'qty': 1,
            'unit': 'job',
            'unit_price': 28000,
            'discount': 0,
            'tax_rate': 18,
            'hsn_sac': '998313'
          },
          {
            'description': 'Maintenance (3 months)',
            'qty': 1,
            'unit': 'lot',
            'unit_price': 9000,
            'discount': 0,
            'tax_rate': 18
          }
        ],
        'totals': {
          'subtotal': 37000,
          'discount_total': 0,
          'tax_total': 6660,
          'shipping': 0,
          'round_off': 0,
          'grand_total': 43660,
          'amount_in_words': 'Forty Three Thousand Six Hundred Sixty Only'
        },
        'terms': {
          'title': 'Terms & Conditions',
          'bullets': [
            'Quotation valid 15 days.',
            '50% advance, balance on delivery.',
            'Taxes extra as applicable.'
          ]
        },
        'notes': _desc.text.trim(),
        'payment': {
          'mode': 'UPI',
          'instructions': '50% advance then delivery',
          'upi_id': seller['bank']?['upi_id'],
          'upi_deeplink': ''
        },
        'branding': {'accent_color': '#0057FF', 'logo_path': '', 'footer_text': ''}
      };

      if (_selectedDoc == 'Quotation') {
        draft = {
          ...draft,
          'quotation': {
            'title': 'Website Redesign Proposal',
            'validity_days': 15,
            'offer_type': 'Fixed bid',
            'pricing_options_enabled': false,
            'advance_percent': 50,
            'delivery_window': '7–10 working days post advance',
            'inclusions': 'Design;Frontend build;QA',
            'exclusions': 'Backend changes;Hosting',
            'assumptions': 'Brand assets provided',
            'warranty_support': '30 days bug-fix',
            'change_requests_rate': '₹1200/hour beyond scope'
          }
        };
      } else if (_selectedDoc == 'Tax Invoice') {
        draft = {
          ...draft,
          'doc_meta': {
            ...draft['doc_meta'],
            'doc_no': 'INV-${DateTime.now().year}-${DateTime.now().millisecond}'
          },
          'invoice': {
            'supply_date': now,
            'bill_to_ship_to_same': true,
            'place_of_supply': 'Maharashtra',
            'reverse_charge': false,
            'irn': '',
            'ack_no': '',
            'ack_date': '',
            'tcs_percent': '',
            'tds_note': 'Customer to deduct TDS u/s 194C @1%',
            'transport_details': '',
            'round_off_enabled': true
          }
        };
      } else if (_selectedDoc == 'Project Brief') {
        draft = {
          ...draft,
          'project_brief': {
            'title': 'Website Redesign — Project Brief',
            'objective': 'Improve conversion rate by 20% within 60 days of launch.',
            'success_metrics': '+20% CVR; <2s LCP',
            'scope': 'Audit current funnel;New landing + checkout;A/B test variants',
            'out_of_scope': 'Backend changes',
            'deliverables': 'Hi-fi designs;Responsive pages;Handover docs',
            'assumptions': 'Existing APIs remain stable',
            'milestones': [
              {'name': 'Discovery', 'start': now, 'end': now, 'fee': 0},
              {
                'name': 'Design',
                'start': DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 3))),
                'end': DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 8))),
                'fee': 18000
              },
              {
                'name': 'Build',
                'start': DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 9))),
                'end': DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 16))),
                'fee': 19000
              }
            ],
            'billing_plan': [
              {'when': 'On acceptance', 'percent': 50},
              {'when': 'On delivery', 'percent': 50}
            ],
            'timeline_days': 17,
            'risks': 'Scope creep;Third-party outages',
            'communication_cadence': 'Weekly check-ins Tue 4 pm IST',
            'change_control': 'Any change via CR signed by both parties',
            'acceptance_criteria': 'Lighthouse score ≥ 90',
            'support_window': '30 days L2 support'
          }
        };
      }

      final box = Hive.box('drafts');
      await box.add({'status': 'generated', 'bundle': draft, 'created': DateTime.now().toIso8601String()});
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => EditorScreen(initialBundle: draft)));
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Error generating draft: \$e')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Widget _docChip(String label, String caption) {
    final selected = label == _selectedDoc;
    return Tooltip(
      message: caption,
      child: ChoiceChip(
        selected: selected,
        onSelected: (_) => setState(() => _selectedDoc = label),
        label: SizedBox(
          width: 160,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: Theme.of(context).textTheme.bodyLarge),
              Text(caption, style: Theme.of(context).textTheme.bodySmall)
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home - Draft')),
      body: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(children: [
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 8),
                  TextField(
                    controller: _desc,
                    maxLines: 5,
                    onChanged: (_) => setState(() {}),
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      labelText: 'Work requirement',
                      hintText:
                          'Describe the work requirement. Include deliverables, timelines, budget hints, and any must-have features. Example: Redesign e-commerce landing, 2-week timeline, budget 40–45k, include 3-month maintenance option, UPI payment preferred.'
                    ),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _docChip('Quotation', 'Price + terms. Includes validity date.'),
                      _docChip('Tax Invoice', 'Final bill with GST breakup and due date.'),
                      _docChip('Project Brief', 'Scope, milestones, billing plan.'),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Flexible(
                        child: DropdownButtonFormField<String>(
                          value: _currency,
                          items: _currencies
                              .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                              .toList(),
                          onChanged: (v) => setState(() => _currency = v ?? 'INR'),
                          decoration: const InputDecoration(labelText: 'Currency'),
                        ),
                      ),
                      const SizedBox(width: 16),
                      TextButton(
                        onPressed: () => Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const SellerSettings()),
                        ),
                        child: const Text('Set Seller Details'),
                      ),
                      const SizedBox(width: 8),
                      TextButton(
                        onPressed: () => Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const ClientsScreen()),
                        ),
                        child: const Text('Saved Clients'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          SizedBox(
            height: 56,
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: _canGenerate ? _generateDraft : null,
                    child: _loading
                        ? const CircularProgressIndicator.adaptive()
                        : const Text('Generate Draft'),
                  ),
                ),
                const SizedBox(width: 12),
                OutlinedButton(
                  child: const Text('History'),
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const HistoryScreen()),
                  ),
                )
              ],
            ),
          )
        ]),
      ),
    );
  }
}
