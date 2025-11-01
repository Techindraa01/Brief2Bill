import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:intl/intl.dart';
import 'package:invoicepdf/Screens/seller_settings_scr.dart';

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
        checkmarkColor: Colors.white,
        selectedColor: Colors.blue.shade800,
        disabledColor: Colors.white,
        side: BorderSide.none,
        selected: selected,
        onSelected: (_) => setState(() => _selectedDoc = label),
        label: SizedBox(
          width: MediaQuery.sizeOf(context).width * 1,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Text(label, style: Theme.of(context).textTheme.bodyLarge),
              // Text(caption, style: Theme.of(context).textTheme.bodySmall)
              Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                  fontFamily: 'Roboto', // replace with your font
                  color: selected ? Colors.white : Colors.black,
                ),
              ),
              Text(
                caption,
                style: TextStyle(
                  fontSize: 12,
                  fontFamily: 'Roboto',
                  color: selected ? Colors.white : Colors.grey.shade500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }


  Widget businessInfo(IconData icon, String title, String subtitle, Color avtarcolor, Color bgcolor){
    return Container(
        decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10)
    ),
    child: Padding(
    padding: const EdgeInsets.all(8.0),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
    children: [
      Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          CircleAvatar(
            backgroundColor: bgcolor, //Colors.blue.shade100,
            child: Icon(icon, size: 20, color: avtarcolor),//Colors.blue.shade600,),
          ),
          SizedBox(width: MediaQuery.widthOf(context) * 0.02,),
          Column(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Text(label, style: Theme.of(context).textTheme.bodyLarge),
                  // Text(caption, style: Theme.of(context).textTheme.bodySmall)
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'Roboto', // replace with your font
                      color: Colors.black,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: TextStyle(
                      fontSize: 12,
                      fontFamily: 'Roboto',
                      color: Colors.grey.shade500,
                    ),
                  ),
                ],
              ),
            ],
          ),

        ],
      ),
      Icon(Icons.arrow_forward_ios, size: 15, color: Colors.blue.shade600,)
    ],
    )));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(title: const Text('Create Invoice', style: TextStyle(color: Colors.white, fontFamily: 'Roboto', fontSize: 16, fontWeight: FontWeight.w600)
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
        leading: IconButton(onPressed: (){}, icon: Icon(Icons.settings,)),
      ),
     //drawer: Drawer(),
      body: Column(children: [
        Expanded(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [

                  SizedBox(height: MediaQuery.heightOf(context) * 0.01),
                  Text("INVOICE TYPE", style: TextStyle(color: Colors.grey.shade600, fontFamily: 'Roboto', fontSize: 12, fontWeight: FontWeight.w600)),
                  SizedBox(height: MediaQuery.heightOf(context) * 0.01),
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10)
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _docChip('Quotation', 'Price + terms. Includes validity date.'),
                          _docChip('Tax Invoice', 'Final bill with GST breakup and due date.'),
                          _docChip('Project Brief', 'Scope, milestones, billing plan.'),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(height: MediaQuery.heightOf(context) * 0.03),
                  Text("BUSINESS INFO", style: TextStyle(color: Colors.grey.shade600, fontFamily: 'Roboto', fontSize: 12, fontWeight: FontWeight.w600)),
                  SizedBox(height: MediaQuery.heightOf(context) * 0.01),
                  Container(
                    decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(10)
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        children: [
                          GestureDetector(
                              onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const SellerSettings()),
                    ),
                              child: businessInfo(Icons.perm_identity, "From", "Add Business Information", Colors.blue.shade600, Colors.blue.shade100)),
                          Divider(color: Colors.grey.shade300,thickness: 1,),
                          GestureDetector(
                              onTap: ()=> Navigator.of(context).push(
                                MaterialPageRoute(builder: (_) => const ClientsScreen()),
                              ),
                              child: businessInfo(Icons.perm_contact_cal_outlined, "To", "Add Client Information", Colors.red.shade600, Colors.red.shade100)),
                          Divider(color: Colors.grey.shade300,thickness: 1,),
                           Padding(
                             padding: const EdgeInsets.only(left: 8, right: 8, bottom: 8, top: 8),
                             child: Row(
                               mainAxisAlignment: MainAxisAlignment.spaceBetween,
                               children: [
                                 CircleAvatar(
                                   backgroundColor: Colors.green.shade100,
                                   child: Icon(Icons.account_balance_wallet_outlined, size: 20, color: Colors.green.shade600,),
                                 ),
                                 SizedBox(width: MediaQuery.widthOf(context) * 0.025,),
                                 Flexible(
                                   child: DropdownButtonFormField<String>(
                                     value: _currency,
                                     items: _currencies
                                         .map((c) => DropdownMenuItem(value: c, child: Text(c, style: TextStyle(color: Colors.black, fontFamily: 'Roboto', fontSize: 14),)))
                                         .toList(),
                                     onChanged: (v) => setState(() => _currency = v ?? 'INR'),
                                     decoration:  InputDecoration(labelText: 'Choose Currency',
                                         labelStyle: TextStyle(color: Colors.grey[600], fontFamily: 'Roboto', fontSize: 16),
                                       border: OutlineInputBorder(
                                         borderSide: BorderSide(color: Colors.grey.shade600, width: 0.5),
                                         borderRadius: BorderRadius.circular(10),
                                       ),
                                       enabledBorder: OutlineInputBorder(
                                         borderSide: BorderSide(color: Colors.grey.shade400, width: 0.8),
                                         borderRadius: BorderRadius.circular(10),
                                       ),
                                       focusedBorder: OutlineInputBorder(
                                         borderSide:  BorderSide(color: Colors.grey.shade400, width: 1.2),
                                         borderRadius: BorderRadius.circular(10),
                                       ), ),
                                   ),
                                 ),
                               ],
                             ),
                           ),

                        ],
                      )
                    ),
                  ),
                  SizedBox(height: MediaQuery.heightOf(context) * 0.03),
                  Text("WORK REQUIREMENT", style: TextStyle(color: Colors.grey.shade600, fontFamily: 'Roboto', fontSize: 12, fontWeight: FontWeight.w600)),
                  SizedBox(height: MediaQuery.heightOf(context) * 0.01),
            Container(
              decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10)
              ),
              child: Padding(
                padding: const EdgeInsets.all(8.0),
                child:
                TextField(
                  controller: _desc,
                  maxLines: 5,
                  onChanged: (_) => setState(() {}),
                  decoration:  InputDecoration(
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(color: Colors.grey.shade400, width: 0.5),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(color: Colors.grey.shade400, width: 0.5),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide:  BorderSide(color: Colors.grey.shade400, width: 0.5),
                      ),
                      hintStyle: TextStyle(color: Colors.grey.shade600, fontFamily: 'Roboto', fontSize: 12, ),
                      hintText:
                      'Describe the work requirement. Include deliverables, timelines, budget hints, and any must-have features. Example: Redesign e-commerce landing, 2-week timeline, budget 40–45k, include 3-month maintenance option, UPI payment preferred.'
                  ),
                ),
              )),
                ],
              ),
            ),
          ),
        ),
        Container(
          color: Colors.white,
          width: double.infinity,
          height: MediaQuery.heightOf(context)* 0.08,
          child: Padding(
            padding: const EdgeInsets.only(left: 10, right: 10),
            child: Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: MediaQuery.heightOf(context)* 0.06,
                    child: ElevatedButton(
                      onPressed: _canGenerate ? _generateDraft : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue.shade800,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10)
                        )
                      ),
                      child: _loading
                          ? const CircularProgressIndicator.adaptive()
                          : Row(
                        spacing: 5,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.drafts, color: Colors.white,),
                          Text('Generate Draft',style: TextStyle(color: Colors.white, fontFamily: 'Roboto', fontSize: 12,fontWeight: FontWeight.w600,),),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                GestureDetector(
                  onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const HistoryScreen()),
              ),
                  child: Container(
                    width: MediaQuery.widthOf(context) * 0.4,
                    height: MediaQuery.heightOf(context)* 0.06,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(10)),
                      child : Row(
                        spacing: 5,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.history_outlined, color: Colors.blue.shade800,),
                          Text('History',style: TextStyle(color: Colors.blue.shade800, fontFamily: 'Roboto', fontSize: 12,fontWeight: FontWeight.w600,),),
                             ],
                      )
                    ),
                ),

              ],
            ),
          ),
        )
      ]),
    );
  }
}
