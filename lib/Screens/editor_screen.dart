import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:hive/hive.dart';
import 'package:intl/intl.dart';
import 'package:invoicepdf/Screens/pdf_gen_screen.dart';
import 'package:invoicepdf/Screens/pdf_preview_scr.dart';

import '../Utils/reusables.dart';

class _ItemControllers {
  final TextEditingController description;
  final TextEditingController hsn;
  final TextEditingController qty;
  final TextEditingController unit;
  final TextEditingController unitPrice;
  final TextEditingController discount;
  final TextEditingController taxRate;

  _ItemControllers.fromItem(Map item)
    : description = TextEditingController(
        text: item['description']?.toString() ?? '',
      ),
      hsn = TextEditingController(text: item['hsn_sac']?.toString() ?? ''),
      qty = TextEditingController(text: item['qty']?.toString() ?? '1'),
      unit = TextEditingController(text: item['unit']?.toString() ?? 'pcs'),
      unitPrice = TextEditingController(
        text: item['unit_price']?.toString() ?? '0',
      ),
      discount = TextEditingController(
        text: item['discount']?.toString() ?? '0',
      ),
      taxRate = TextEditingController(
        text: item['tax_rate']?.toString() ?? '0',
      );

  Map<String, dynamic> toMap() {
    double parseDecimal(TextEditingController c) =>
        double.tryParse(c.text.trim()) ?? 0;
    return {
      'description': description.text.trim(),
      'hsn_sac': hsn.text.trim(),
      'qty': double.tryParse(qty.text.trim()) ?? 0,
      'unit': unit.text.trim().isEmpty ? 'pcs' : unit.text.trim(),
      'unit_price': parseDecimal(unitPrice),
      'discount': parseDecimal(discount),
      'tax_rate': double.tryParse(taxRate.text.trim()) ?? 0,
    };
  }

  void dispose() {
    description.dispose();
    hsn.dispose();
    qty.dispose();
    unit.dispose();
    unitPrice.dispose();
    discount.dispose();
    taxRate.dispose();
  }
}

class _MilestoneControllers {
  final TextEditingController name;
  final TextEditingController start;
  final TextEditingController end;
  final TextEditingController fee;

  _MilestoneControllers.from(Map milestone)
    : name = TextEditingController(text: milestone['name']?.toString() ?? ''),
      start = TextEditingController(text: milestone['start']?.toString() ?? ''),
      end = TextEditingController(text: milestone['end']?.toString() ?? ''),
      fee = TextEditingController(text: milestone['fee']?.toString() ?? '0');

  Map<String, dynamic> toMap() => {
    'name': name.text.trim(),
    'start': start.text.trim(),
    'end': end.text.trim(),
    'fee': double.tryParse(fee.text.trim()) ?? 0,
  };

  void dispose() {
    name.dispose();
    start.dispose();
    end.dispose();
    fee.dispose();
  }
}

class _BillingPartControllers {
  final TextEditingController when;
  final TextEditingController percent;

  _BillingPartControllers.from(Map part)
    : when = TextEditingController(text: part['when']?.toString() ?? ''),
      percent = TextEditingController(text: part['percent']?.toString() ?? '0');

  Map<String, dynamic> toMap() => {
    'when': when.text.trim(),
    'percent': int.tryParse(percent.text.trim()) ?? 0,
  };

  void dispose() {
    when.dispose();
    percent.dispose();
  }
}

class EditorScreen extends StatefulWidget {
  final Map initialBundle;

  const EditorScreen({super.key, required this.initialBundle});

  @override
  State<EditorScreen> createState() => _EditorScreenState();
}

class _EditorScreenState extends State<EditorScreen> {
  final _formKey = GlobalKey<FormState>();
  late Map<String, dynamic> bundle;
  final _controllers = <String, TextEditingController>{};
  late List<_ItemControllers> _itemControllers;
  late List<_MilestoneControllers> _milestoneControllers;
  late List<_BillingPartControllers> _billingControllers;
  String _paymentMode = 'UPI';
  bool _pricingOptionsEnabled = false;
  bool _billToShipSame = true;
  bool _reverseCharge = false;
  bool _roundOffEnabled = true;
  bool _discountAmountOnly = true;

  String get _docType => (bundle['doc_type'] ?? 'QUOTATION').toString();

  DateTime? _parseDate(dynamic value) {
    if (value == null) {
      return null;
    }
    if (value is DateTime) {
      return value;
    }
    final raw = value.toString();
    if (raw.isEmpty) {
      return null;
    }
    return DateTime.tryParse(raw);
  }

  @override
  void initState() {
    super.initState();
    bundle =
        jsonDecode(jsonEncode(widget.initialBundle)) as Map<String, dynamic>;
    _initControllers();
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    for (final ic in _itemControllers) {
      ic.dispose();
    }
    for (final mc in _milestoneControllers) {
      mc.dispose();
    }
    for (final bc in _billingControllers) {
      bc.dispose();
    }
    super.dispose();
  }

  void _initControllers() {
    _controllers.clear();
    final seller = Map<String, dynamic>.from(bundle['seller'] ?? {});
    final sellerBank = Map<String, dynamic>.from(seller['bank'] ?? {});
    final buyer = Map<String, dynamic>.from(bundle['buyer'] ?? {});
    final docMeta = Map<String, dynamic>.from(bundle['doc_meta'] ?? {});
    final dates = Map<String, dynamic>.from(bundle['dates'] ?? {});
    final totals = Map<String, dynamic>.from(bundle['totals'] ?? {});
    final payment = Map<String, dynamic>.from(bundle['payment'] ?? {});
    final terms = Map<String, dynamic>.from(bundle['terms'] ?? {});
    final branding = Map<String, dynamic>.from(bundle['branding'] ?? {});
    final quotation = Map<String, dynamic>.from(bundle['quotation'] ?? {});
    final invoice = Map<String, dynamic>.from(bundle['invoice'] ?? {});
    final projectBrief = Map<String, dynamic>.from(
      bundle['project_brief'] ?? {},
    );

    String joinList(dynamic value) {
      if (value is List) {
        return value.map((e) => e.toString()).join('\n');
      }
      return value?.toString() ?? '';
    }

    void setController(String key, dynamic value) {
      _controllers[key]?.dispose();
      _controllers[key] = TextEditingController(text: value?.toString() ?? '');
    }

    setController('seller_name', seller['name']);
    setController('seller_address', seller['address']);
    setController('seller_email', seller['email']);
    setController('seller_phone', seller['phone']);
    setController('seller_gstin', seller['gstin']);
    setController('seller_pan', seller['pan']);
    setController('seller_bank_account_name', sellerBank['account_name']);
    setController('seller_bank_account_no', sellerBank['account_no']);
    setController('seller_bank_ifsc', sellerBank['ifsc']);
    setController('seller_bank_upi', sellerBank['upi_id']);

    setController('buyer_name', buyer['name']);
    setController('buyer_email', buyer['email']);
    setController('buyer_phone', buyer['phone']);
    setController('buyer_address', buyer['address']);
    setController('buyer_gstin', buyer['gstin']);

    setController('doc_no', docMeta['doc_no']);
    setController('ref_no', docMeta['ref_no']);
    setController('po_no', docMeta['po_no']);
    setController('issue_date', dates['issue_date']);
    setController('due_date', dates['due_date']);
    setController('valid_till', dates['valid_till']);

    setController('totals_shipping', totals['shipping']);
    setController('totals_round_off', totals['round_off']);
    setController('totals_amount_in_words', totals['amount_in_words']);

    _paymentMode = payment['mode']?.toString() ?? 'UPI';
    setController('payment_instructions', payment['instructions']);
    setController('payment_upi', payment['upi_id'] ?? payment['upi'] ?? '');
    setController('payment_deeplink', payment['upi_deeplink']);

    setController('terms_title', terms['title'] ?? 'Terms & Conditions');
    setController('terms_bullets', joinList(terms['bullets']));
    setController('notes', bundle['notes']);

    setController('branding_accent', branding['accent_color']);
    setController('branding_footer', branding['footer_text']);
    setController('branding_logo', branding['logo_path']);

    setController('quotation_title', quotation['title']);
    setController('quotation_validity_days', quotation['validity_days']);
    setController('quotation_offer_type', quotation['offer_type']);
    _pricingOptionsEnabled = quotation['pricing_options_enabled'] == true;
    setController('quotation_advance_percent', quotation['advance_percent']);
    setController('quotation_delivery_window', quotation['delivery_window']);
    setController('quotation_inclusions', joinList(quotation['inclusions']));
    setController('quotation_exclusions', joinList(quotation['exclusions']));
    setController('quotation_assumptions', joinList(quotation['assumptions']));
    setController('quotation_warranty', quotation['warranty_support']);
    setController('quotation_change_rate', quotation['change_requests_rate']);

    setController('invoice_supply_date', invoice['supply_date']);
    _billToShipSame = invoice['bill_to_ship_to_same'] != false;
    setController('invoice_ship_to', invoice['ship_to_address'] ?? '');
    setController('invoice_place_of_supply', invoice['place_of_supply']);
    _reverseCharge = invoice['reverse_charge'] == true;
    setController('invoice_irn', invoice['irn']);
    setController('invoice_ack_no', invoice['ack_no']);
    setController('invoice_ack_date', invoice['ack_date']);
    setController('invoice_tcs_percent', invoice['tcs_percent']);
    setController('invoice_tds_note', invoice['tds_note']);
    setController('invoice_transport', invoice['transport_details']);
    _roundOffEnabled = invoice['round_off_enabled'] != false;

    setController('brief_title', projectBrief['title']);
    setController('brief_objective', projectBrief['objective']);
    setController(
      'brief_success_metrics',
      joinList(projectBrief['success_metrics']),
    );
    setController('brief_scope', joinList(projectBrief['scope']));
    setController('brief_out_scope', joinList(projectBrief['out_of_scope']));
    setController('brief_deliverables', joinList(projectBrief['deliverables']));
    setController('brief_assumptions', joinList(projectBrief['assumptions']));
    setController('brief_timeline_days', projectBrief['timeline_days']);
    setController('brief_risks', joinList(projectBrief['risks']));
    setController('brief_communication', projectBrief['communication_cadence']);
    setController('brief_change_control', projectBrief['change_control']);
    setController(
      'brief_acceptance',
      joinList(projectBrief['acceptance_criteria']),
    );
    setController('brief_support_window', projectBrief['support_window']);

    _itemControllers =
        (bundle['items'] as List?)
            ?.map(
              (e) => _ItemControllers.fromItem(Map<String, dynamic>.from(e)),
            )
            .toList() ??
        [
          _ItemControllers.fromItem({
            'description': 'New item',
            'qty': 1,
            'unit': 'pcs',
            'unit_price': 0,
            'discount': 0,
            'tax_rate': 0,
          }),
        ];

    _milestoneControllers =
        (projectBrief['milestones'] as List?)
            ?.map(
              (e) => _MilestoneControllers.from(Map<String, dynamic>.from(e)),
            )
            .toList() ??
        [
          _MilestoneControllers.from({
            'name': 'Kick-off',
            'start': dates['issue_date'] ?? '',
            'end': dates['issue_date'] ?? '',
            'fee': 0,
          }),
        ];

    _billingControllers =
        (projectBrief['billing_plan'] as List?)
            ?.map(
              (e) => _BillingPartControllers.from(Map<String, dynamic>.from(e)),
            )
            .toList() ??
        [
          _BillingPartControllers.from({
            'when': 'On acceptance',
            'percent': 50,
          }),
          _BillingPartControllers.from({'when': 'On delivery', 'percent': 50}),
        ];
  }

  Future<void> _pickDate(TextEditingController controller) async {
    final initial = controller.text.trim().isEmpty
        ? DateTime.now()
        : DateTime.tryParse(controller.text.trim()) ?? DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      controller.text = DateFormat('yyyy-MM-dd').format(picked);
      setState(() {});
    }
  }

  bool _applyForm({bool validate = true}) {
    final formState = _formKey.currentState;
    if (validate && !(formState?.validate() ?? false)) {
      return false;
    }
    formState?.save();

    final seller = {
      'name': _controllers['seller_name']!.text.trim(),
      'address': _controllers['seller_address']!.text.trim(),
      'email': _controllers['seller_email']!.text.trim(),
      'phone': _controllers['seller_phone']!.text.trim(),
      'gstin': _controllers['seller_gstin']!.text.trim(),
      'pan': _controllers['seller_pan']!.text.trim(),
      'bank': {
        'account_name': _controllers['seller_bank_account_name']!.text.trim(),
        'account_no': _controllers['seller_bank_account_no']!.text.trim(),
        'ifsc': _controllers['seller_bank_ifsc']!.text.trim(),
        'upi_id': _controllers['seller_bank_upi']!.text.trim(),
      },
    };

    final buyer = {
      'name': _controllers['buyer_name']!.text.trim(),
      'email': _controllers['buyer_email']!.text.trim(),
      'phone': _controllers['buyer_phone']!.text.trim(),
      'address': _controllers['buyer_address']!.text.trim(),
      'gstin': _controllers['buyer_gstin']!.text.trim(),
    };

    final docMeta = {
      'doc_no': _controllers['doc_no']!.text.trim(),
      'ref_no': _controllers['ref_no']!.text.trim(),
      'po_no': _controllers['po_no']!.text.trim(),
    };

    final dates = {
      'issue_date': _controllers['issue_date']!.text.trim(),
      'due_date': _controllers['due_date']!.text.trim(),
      'valid_till': _controllers['valid_till']!.text.trim(),
    };

    final items = _itemControllers.map((ic) => ic.toMap()).toList();

    if (items.isEmpty ||
        items.any((i) => i['description'].toString().isEmpty)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Add at least one item with description.'),
        ),
      );
      return false;
    }

    for (final item in items) {
      final qty = (item['qty'] as num?) ?? 0;
      final unitPrice = (item['unit_price'] as num?) ?? 0;
      final discount = (item['discount'] as num?) ?? 0;
      if (qty <= 0) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Quantity must be positive for "${item['description']}".',
            ),
          ),
        );
        return false;
      }
      if (discount < 0 || discount > qty * unitPrice) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Discount for "${item['description']}" exceeds line amount.',
            ),
          ),
        );
        return false;
      }
    }

    final totals = Map<String, dynamic>.from(bundle['totals'] ?? {});
    totals['shipping'] =
        double.tryParse(_controllers['totals_shipping']!.text.trim()) ?? 0;
    totals['round_off'] =
        double.tryParse(_controllers['totals_round_off']!.text.trim()) ?? 0;
    totals['amount_in_words'] = _controllers['totals_amount_in_words']!.text
        .trim();

    final payment = {
      'mode': _paymentMode,
      'instructions': _controllers['payment_instructions']!.text.trim(),
      'upi_id': _controllers['payment_upi']!.text.trim(),
      'upi_deeplink': _controllers['payment_deeplink']!.text.trim(),
    };

    List<String> splitList(String key) {
      final value = _controllers[key]?.text ?? '';
      return value
          .split('\n')
          .map((e) => e.trim())
          .where((element) => element.isNotEmpty)
          .toList();
    }

    final terms = {
      'title': _controllers['terms_title']!.text.trim().isEmpty
          ? 'Terms & Conditions'
          : _controllers['terms_title']!.text.trim(),
      'bullets': splitList('terms_bullets'),
    };

    final quotation = {
      'title': _controllers['quotation_title']!.text.trim(),
      'validity_days': int.tryParse(
        _controllers['quotation_validity_days']!.text.trim(),
      ),
      'offer_type': _controllers['quotation_offer_type']!.text.trim(),
      'pricing_options_enabled': _pricingOptionsEnabled,
      'advance_percent': int.tryParse(
        _controllers['quotation_advance_percent']!.text.trim(),
      ),
      'delivery_window': _controllers['quotation_delivery_window']!.text.trim(),
      'inclusions': splitList('quotation_inclusions'),
      'exclusions': splitList('quotation_exclusions'),
      'assumptions': splitList('quotation_assumptions'),
      'warranty_support': _controllers['quotation_warranty']!.text.trim(),
      'change_requests_rate': _controllers['quotation_change_rate']!.text
          .trim(),
    };

    final invoice = {
      'supply_date': _controllers['invoice_supply_date']!.text.trim(),
      'bill_to_ship_to_same': _billToShipSame,
      'ship_to_address': _billToShipSame
          ? ''
          : _controllers['invoice_ship_to']!.text.trim(),
      'place_of_supply': _controllers['invoice_place_of_supply']!.text.trim(),
      'reverse_charge': _reverseCharge,
      'irn': _controllers['invoice_irn']!.text.trim(),
      'ack_no': _controllers['invoice_ack_no']!.text.trim(),
      'ack_date': _controllers['invoice_ack_date']!.text.trim(),
      'tcs_percent': _controllers['invoice_tcs_percent']!.text.trim(),
      'tds_note': _controllers['invoice_tds_note']!.text.trim(),
      'transport_details': _controllers['invoice_transport']!.text.trim(),
      'round_off_enabled': _roundOffEnabled,
    };

    final projectBrief = {
      'title': _controllers['brief_title']!.text.trim(),
      'objective': _controllers['brief_objective']!.text.trim(),
      'success_metrics': splitList('brief_success_metrics'),
      'scope': splitList('brief_scope'),
      'out_of_scope': splitList('brief_out_scope'),
      'deliverables': splitList('brief_deliverables'),
      'assumptions': splitList('brief_assumptions'),
      'milestones': _milestoneControllers.map((e) => e.toMap()).toList(),
      'billing_plan': _billingControllers.map((e) => e.toMap()).toList(),
      'timeline_days':
          int.tryParse(_controllers['brief_timeline_days']!.text.trim()) ?? 0,
      'risks': splitList('brief_risks'),
      'communication_cadence': _controllers['brief_communication']!.text.trim(),
      'change_control': _controllers['brief_change_control']!.text.trim(),
      'acceptance_criteria': splitList('brief_acceptance'),
      'support_window': _controllers['brief_support_window']!.text.trim(),
    };

    if (seller['name'].toString().isEmpty ||
        seller['name'].toString().length < 2) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Seller business name is required (2-100 characters).'),
        ),
      );
      return false;
    }
    if (buyer['name'].toString().isEmpty ||
        buyer['name'].toString().length < 2) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Buyer name is required (2-100 characters).'),
        ),
      );
      return false;
    }

    final issue = _parseDate(dates['issue_date']);
    final due = _parseDate(dates['due_date']);
    final validTill = _parseDate(dates['valid_till']);
    if (issue != null) {
      if (due != null && due.isBefore(issue)) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Due date must be on or after issue date.'),
          ),
        );
        return false;
      }
      if (validTill != null && validTill.isBefore(issue)) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Valid till date must be on or after issue date.'),
          ),
        );
        return false;
      }
    }

    if (_docType == 'TAX INVOICE' && docMeta['doc_no'].toString().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Invoice number is required for tax invoices.'),
        ),
      );
      return false;
    }

    if (_docType == 'PROJECT BRIEF') {
      if (projectBrief['title'].toString().isEmpty ||
          projectBrief['objective'].toString().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Project brief requires a title and objective.'),
          ),
        );
        return false;
      }
      if ((projectBrief['scope'] as List).isEmpty ||
          (projectBrief['deliverables'] as List).isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Add at least one scope item and deliverable.'),
          ),
        );
        return false;
      }
      if ((projectBrief['milestones'] as List).isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Add at least one milestone.')),
        );
        return false;
      }
      if ((projectBrief['billing_plan'] as List).isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Add billing plan parts totaling 100%.'),
          ),
        );
        return false;
      }
      final billingTotal = (projectBrief['billing_plan'] as List)
          .map((e) => (e['percent'] as num?) ?? 0)
          .fold<int>(0, (prev, element) => prev + element.toInt());
      if (billingTotal != 100) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Billing plan percentages must total 100 (current: $billingTotal).',
            ),
          ),
        );
        return false;
      }
      for (final milestone in projectBrief['milestones'] as List) {
        final start = _parseDate(milestone['start']);
        final end = _parseDate(milestone['end']);
        if (start != null && end != null && end.isBefore(start)) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                'Milestone "${milestone['name']}" end date must be on or after start.',
              ),
            ),
          );
          return false;
        }
      }
      if ((projectBrief['timeline_days'] as num) <= 0) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Timeline days must be greater than zero.'),
          ),
        );
        return false;
      }
    }

    bundle['seller'] = seller;
    bundle['buyer'] = buyer;
    bundle['doc_meta'] = docMeta;
    bundle['dates'] = dates;
    bundle['items'] = items;
    bundle['totals'] = totals;
    bundle['payment'] = payment;
    bundle['terms'] = terms;
    bundle['branding'] = {
      'accent_color': _controllers['branding_accent']!.text.trim(),
      'footer_text': _controllers['branding_footer']!.text.trim(),
      'logo_path': _controllers['branding_logo']!.text.trim(),
    };
    bundle['notes'] = _controllers['notes']!.text.trim();

    if (_docType == 'QUOTATION') {
      bundle['quotation'] = quotation;
    }
    if (_docType == 'TAX INVOICE') {
      bundle['invoice'] = invoice;
    }
    if (_docType == 'PROJECT BRIEF') {
      bundle['project_brief'] = projectBrief;
    }
    return true;
  }

  void _recalculateTotals() {
    if (!_applyForm(validate: false)) return;
    double subtotal = 0;
    double discountTotal = 0;
    double taxTotal = 0;
    for (final item in (bundle['items'] as List).cast<Map>()) {
      final qty = (item['qty'] as num?) ?? 0;
      final price = (item['unit_price'] as num?) ?? 0;
      final discount = (item['discount'] as num?) ?? 0;
      final tax = (item['tax_rate'] as num?) ?? 0;
      final line = qty * price;
      subtotal += line;
      discountTotal += discount;
      taxTotal += ((line - discount) * tax / 100);
    }
    final totals = Map<String, dynamic>.from(bundle['totals'] ?? {});
    totals['subtotal'] = double.parse(subtotal.toStringAsFixed(2));
    totals['discount_total'] = double.parse(discountTotal.toStringAsFixed(2));
    totals['tax_total'] = double.parse(taxTotal.toStringAsFixed(2));
    final shipping = (totals['shipping'] as num?) ?? 0;
    final roundOff = _roundOffEnabled ? (totals['round_off'] as num?) ?? 0 : 0;
    totals['grand_total'] = double.parse(
      (subtotal - discountTotal + taxTotal + shipping + roundOff)
          .toStringAsFixed(2),
    );
    bundle['totals'] = totals;
    setState(() {});
  }

  void _addItem() {
    setState(() {
      _itemControllers.add(
        _ItemControllers.fromItem({
          'description': 'New item',
          'qty': 1,
          'unit': 'pcs',
          'unit_price': 0,
          'discount': 0,
          'tax_rate': 0,
        }),
      );
    });
  }

  void _removeItem(int index) {
    if (_itemControllers.length == 1) return;
    setState(() {
      _itemControllers.removeAt(index).dispose();
    });
  }

  void _addMilestone() {
    setState(() {
      _milestoneControllers.add(
        _MilestoneControllers.from({
          'name': '',
          'start': '',
          'end': '',
          'fee': 0,
        }),
      );
    });
  }

  void _removeMilestone(int index) {
    if (_milestoneControllers.length == 1) return;
    setState(() {
      _milestoneControllers.removeAt(index).dispose();
    });
  }

  void _addBillingPart() {
    setState(() {
      _billingControllers.add(
        _BillingPartControllers.from({'when': '', 'percent': 0}),
      );
    });
  }

  void _removeBillingPart(int index) {
    if (_billingControllers.length == 1) return;
    setState(() {
      _billingControllers.removeAt(index).dispose();
    });
  }

  Future<void> _previewPdf() async {
    if (!_applyForm()) return;
    final pdf = await PDFGenerator.buildPdf(bundle);
    await Hive.box(
      'history',
    ).add({'bundle': bundle, 'created': DateTime.now().toIso8601String()});
    if (!mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PdfPreviewScreen(document: pdf, bundle: bundle),
      ),
    );
  }

  Future<void> _exportPdf() async {
    if (!_applyForm()) return;
    final pdf = await PDFGenerator.buildPdf(bundle);
    await Hive.box('history').add({
      'bundle': bundle,
      'created': DateTime.now().toIso8601String(),
      'type': 'export',
    });
    if (!mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PdfPreviewScreen(document: pdf, bundle: bundle),
      ),
    );
  }

  Future<void> _share() async {
    if (!_applyForm()) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Share flow will be implemented in the mobile shell.'),
      ),
    );
  }

  void _resetToAIDraft() {
    bundle =
        jsonDecode(jsonEncode(widget.initialBundle)) as Map<String, dynamic>;
    _initControllers();
    setState(() {});
  }

  void _duplicateAs(String targetDocType) {
    setState(() {
      bundle['doc_type'] = targetDocType;
      if (targetDocType == 'QUOTATION') {
        bundle['quotation'] ??= {};
      } else if (targetDocType == 'TAX INVOICE') {
        bundle['invoice'] ??= {};
      } else if (targetDocType == 'PROJECT BRIEF') {
        bundle['project_brief'] ??= {};
      }
      _initControllers();
    });
  }

  void _generatePayLink() {
    if (!_applyForm()) return;
    final upi = bundle['payment']?['upi_id']?.toString() ?? '';
    final upiRegex = RegExp(r'^[\w\.\-]{2,}@\w{2,}$');
    if (upi.isEmpty || !upiRegex.hasMatch(upi)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Enter a valid UPI ID before generating the pay link.'),
        ),
      );
      return;
    }
    final amount = (bundle['totals']?['grand_total'] as num?) ?? 0;
    final docNo = bundle['doc_meta']?['doc_no'] ?? 'DOC';
    final seller = bundle['seller']?['name'] ?? '';
    final deeplink =
        'upi://pay?pa=$upi&pn=${Uri.encodeComponent(seller)}&am=${amount.toStringAsFixed(2)}&cu=${bundle['currency'] ?? 'INR'}&tn=${Uri.encodeComponent('Payment for $docNo')}&tr=$docNo';
    _controllers['payment_deeplink']!.text = deeplink;
    bundle['payment'] = {
      ...(bundle['payment'] ?? {}),
      'upi_deeplink': deeplink,
    };
    setState(() {});
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Pay link generated.')));
  }

  Future<void> _copyDeeplink() async {
    if (_controllers['payment_deeplink']!.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Generate a pay link before copying.')),
      );
      return;
    }
    await Clipboard.setData(
      ClipboardData(text: _controllers['payment_deeplink']!.text.trim()),
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('UPI deeplink copied to clipboard.')),
    );
  }

  String _sectionTitle(String label) => label.toUpperCase();

  Widget _buildTextField(
    String key,
    String label, {
    String? hint,
    bool requiredField = false,
    TextInputType inputType = TextInputType.text,
    int maxLines = 1,
    bool readOnly = false,
    VoidCallback? onTap,
    String? Function(String?)? validator,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: _controllers[key],
        readOnly: readOnly,
        maxLines: maxLines,
        keyboardType: inputType,
        onTap: onTap,
        style: TextStyle(fontFamily: 'Roboto', fontSize: 14),
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          isDense: true,
          contentPadding: const EdgeInsets.symmetric(
            vertical: 10,
            horizontal: 12,
          ),
          suffixIcon: onTap != null
              ? const Icon(Icons.calendar_today_outlined)
              : null,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade400, width: 1),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade400, width: 1),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade600, width: 2),
          ),
        ),
        validator:
            validator ??
            (value) {
              final trimmed = value?.trim() ?? '';
              if (requiredField && trimmed.isEmpty) {
                return '$label is required';
              }
              return null;
            },
      ),
    );
  }

  List<Widget> _buildItemRows() {
    return List.generate(_itemControllers.length, (index) {
      final ic = _itemControllers[index];
      return Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(height: 10),
                TextFormField(
                  controller: ic.description,
                  decoration: InputDecoration(
                    labelText: 'Description *',
                    isDense: true,
                    contentPadding: EdgeInsets.symmetric(
                      vertical: 10,
                      horizontal: 12,
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide(
                        color: Colors.grey.shade400,
                        width: 1,
                      ),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide(
                        color: Colors.grey.shade400,
                        width: 1,
                      ),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide(
                        color: Colors.grey.shade600,
                        width: 2,
                      ),
                    ),
                  ),
                  validator: (value) => (value?.trim().isEmpty ?? true)
                      ? 'Description is required'
                      : null,
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: ic.qty,
                        decoration: InputDecoration(
                          labelText: 'Quantity *',
                          isDense: true,
                          contentPadding: EdgeInsets.symmetric(
                            vertical: 10,
                            horizontal: 12,
                          ),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade600,
                              width: 2,
                            ),
                          ),
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextFormField(
                        controller: ic.unit,
                        decoration: InputDecoration(
                          labelText: 'Unit',
                          isDense: true,
                          contentPadding: EdgeInsets.symmetric(
                            vertical: 10,
                            horizontal: 12,
                          ),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade600,
                              width: 2,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: ic.unitPrice,
                        decoration: InputDecoration(
                          labelText: 'Unit price *',
                          isDense: true,
                          contentPadding: EdgeInsets.symmetric(
                            vertical: 10,
                            horizontal: 12,
                          ),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade600,
                              width: 2,
                            ),
                          ),
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextFormField(
                        controller: ic.discount,
                        decoration: InputDecoration(
                          labelText: 'Discount',
                          isDense: true,
                          contentPadding: EdgeInsets.symmetric(
                            vertical: 10,
                            horizontal: 12,
                          ),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade600,
                              width: 2,
                            ),
                          ),
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextFormField(
                        controller: ic.taxRate,
                        decoration: InputDecoration(
                          labelText: 'Tax rate %',
                          isDense: true,
                          contentPadding: EdgeInsets.symmetric(
                            vertical: 10,
                            horizontal: 12,
                          ),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade600,
                              width: 2,
                            ),
                          ),
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: ic.hsn,
                  decoration: InputDecoration(
                    labelText: 'HSN/SAC',
                    isDense: true,
                    contentPadding: EdgeInsets.symmetric(
                      vertical: 10,
                      horizontal: 12,
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide(
                        color: Colors.grey.shade400,
                        width: 1,
                      ),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide(
                        color: Colors.grey.shade400,
                        width: 1,
                      ),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide(
                        color: Colors.grey.shade600,
                        width: 2,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    if (_itemControllers.length > 1)
                      TextButton.icon(
                        onPressed: () => _removeItem(index),
                        icon: const Icon(
                          Icons.delete_outline,
                          color: Colors.red,
                        ),
                        label: const Text(
                          'Remove line',
                          style: TextStyle(
                            color: Colors.red,
                            fontWeight: FontWeight.w600,
                            fontFamily: 'Roboto',
                          ),
                        ),
                      ),
                    const Spacer(),
                    IconButton(
                      tooltip: 'Duplicate line',
                      onPressed: () {
                        setState(() {
                          _itemControllers.insert(
                            index + 1,
                            _ItemControllers.fromItem(
                              _itemControllers[index].toMap(),
                            ),
                          );
                        });
                      },
                      icon: Icon(Icons.copy, color: Colors.blue[700], size: 20),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      );
    });
  }

  List<Widget> _buildMilestoneRows() {
    return List.generate(_milestoneControllers.length, (index) {
      final mc = _milestoneControllers[index];
      return Container(
        decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(10)
        ),
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            children: [
              TextFormField(
                controller: mc.name,
                decoration:  InputDecoration(
                  labelText: 'Milestone name *',
                  isDense: true,
                  contentPadding: EdgeInsets.symmetric(
                    vertical: 10,
                    horizontal: 12,
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: BorderSide(
                      color: Colors.grey.shade400,
                      width: 1,
                    ),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: BorderSide(
                      color: Colors.grey.shade400,
                      width: 1,
                    ),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: BorderSide(
                      color: Colors.grey.shade600,
                      width: 2,
                    ),
                  ),
                ),
                validator: (value) => (value?.trim().isEmpty ?? true)
                    ? 'Milestone name required'
                    : null,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: mc.start,
                      readOnly: true,
                      decoration: InputDecoration(
                        labelText: 'Start date *',
                        isDense: true,
                        contentPadding: EdgeInsets.symmetric(
                          vertical: 10,
                          horizontal: 12,
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(
                            color: Colors.grey.shade400,
                            width: 1,
                          ),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(
                            color: Colors.grey.shade400,
                            width: 1,
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(
                            color: Colors.grey.shade600,
                            width: 2,
                          ),
                        ),
                      ),
                      onTap: () => _pickDate(mc.start),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextFormField(
                      controller: mc.end,
                      readOnly: true,
                      decoration:  InputDecoration(
                        labelText: 'End date *',
                        isDense: true,
                        contentPadding: EdgeInsets.symmetric(
                          vertical: 10,
                          horizontal: 12,
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(
                            color: Colors.grey.shade400,
                            width: 1,
                          ),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(
                            color: Colors.grey.shade400,
                            width: 1,
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(
                            color: Colors.grey.shade600,
                            width: 2,
                          ),
                        ),
                      ),
                      onTap: () => _pickDate(mc.end),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextFormField(
                      controller: mc.fee,
                      decoration:  InputDecoration(labelText: 'Fee', isDense: true,
                        contentPadding: EdgeInsets.symmetric(
                          vertical: 10,
                          horizontal: 12,
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(
                            color: Colors.grey.shade400,
                            width: 1,
                          ),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(
                            color: Colors.grey.shade400,
                            width: 1,
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(
                            color: Colors.grey.shade600,
                            width: 2,
                          ),
                        ),),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (_milestoneControllers.length > 1)
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton.icon(
                    onPressed: () => _removeMilestone(index),
                    icon: const Icon(Icons.delete_outline),
                    label: const Text('Remove milestone'),
                  ),
                ),
            ],
          ),
        ),
      );
    });
  }

  List<Widget> _buildBillingRows() {
    return List.generate(_billingControllers.length, (index) {
      final bc = _billingControllers[index];
      return Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Container(
          decoration: BoxDecoration(
              color: Colors.grey.shade100,
              borderRadius: BorderRadius.circular(10)
          ),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Row(
              children: [
                Expanded(
                  flex: 2,
                  child: TextFormField(
                    controller: bc.when,
                    decoration:  InputDecoration(
                      labelText: 'Billing trigger *',
                      isDense: true,
                      contentPadding: EdgeInsets.symmetric(
                        vertical: 10,
                        horizontal: 10,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(
                          color: Colors.grey.shade400,
                          width: 1,
                        ),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(
                          color: Colors.grey.shade400,
                          width: 1,
                        ),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(
                          color: Colors.grey.shade600,
                          width: 2,
                        ),
                      ),
                    ),
                    validator: (value) => (value?.trim().isEmpty ?? true)
                        ? 'Provide the trigger'
                        : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: bc.percent,
                    decoration:  InputDecoration(labelText: 'Percent *',
                      isDense: true,
                      contentPadding: EdgeInsets.symmetric(
                        vertical: 10,
                        horizontal: 12,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(
                          color: Colors.grey.shade400,
                          width: 1,
                        ),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(
                          color: Colors.grey.shade400,
                          width: 1,
                        ),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(
                          color: Colors.grey.shade600,
                          width: 2,
                        ),
                      ),

                    ),
                    keyboardType: TextInputType.number,
                  ),
                ),
                if (_billingControllers.length > 1)
                  IconButton(
                    onPressed: () => _removeBillingPart(index),
                    icon: const Icon(Icons.delete_outline),
                  ),
              ],
            ),
          ),
        ),
      );
    });
  }

  PopupMenuButton<String> _buildOverflowMenu() {
    return PopupMenuButton<String>(
      onSelected: (value) {
        switch (value) {
          case 'duplicate_quote':
            _duplicateAs('QUOTATION');
            break;
          case 'duplicate_invoice':
            _duplicateAs('TAX INVOICE');
            break;
          case 'duplicate_brief':
            _duplicateAs('PROJECT BRIEF');
            break;
          case 'reset':
            _resetToAIDraft();
            break;
        }
      },
      itemBuilder: (context) => [
        const PopupMenuItem(
          value: 'duplicate_quote',
          child: Text('Duplicate as Quotation'),
        ),
        const PopupMenuItem(
          value: 'duplicate_invoice',
          child: Text('Duplicate as Tax Invoice'),
        ),
        const PopupMenuItem(
          value: 'duplicate_brief',
          child: Text('Duplicate as Project Brief'),
        ),
        const PopupMenuDivider(),
        const PopupMenuItem(value: 'reset', child: Text('Reset to AI draft')),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final totals = Map<String, dynamic>.from(bundle['totals'] ?? {});
    final currency = bundle['currency']?.toString() ?? 'INR';
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text(
          'Editor',
          style: TextStyle(
            color: Colors.white,
            fontFamily: 'Roboto',
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        flexibleSpace: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
              colors: <Color>[Colors.blue.shade800, Colors.blue.shade900],
            ),
          ),
        ),
        centerTitle: true,
        iconTheme: IconThemeData(color: Colors.white),
          actions: [
            TextButton(onPressed: _recalculateTotals, child: const Text('Recalculate Totals',style: TextStyle(
              color: Colors.white,
              fontFamily: 'Roboto',
              fontSize: 14,
            ),)),
            TextButton(onPressed: _previewPdf, child: const Text('Preview PDF',style: TextStyle(
              color: Colors.white,
              fontFamily: 'Roboto',
              fontSize: 14,
            ),)),
            _buildOverflowMenu(),
          ],
      ),
      // appBar: AppBar(
      //   title: Text('Editor • ${_docType.replaceAll('_', ' ')}'),
      //   actions: [
      //     TextButton(onPressed: _recalculateTotals, child: const Text('Recalculate totals')),
      //     TextButton(onPressed: _previewPdf, child: const Text('Preview PDF')),
      //     _buildOverflowMenu(),
      //   ],
      // ),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _sectionTitle('Seller block'),
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontFamily: 'Roboto',
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),

              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Column(
                    children: [
                      SizedBox(height: 10),
                      _buildTextField(
                        'seller_name',
                        'Business name',
                        requiredField: true,
                        validator: (value) {
                          final trimmed = value?.trim() ?? '';
                          if (trimmed.isEmpty)
                            return 'Business name is required';
                          if (trimmed.length < 2 || trimmed.length > 100) {
                            return 'Must be 2-100 characters';
                          }
                          return null;
                        },
                      ),
                      _buildTextField(
                        'seller_address',
                        'Address',
                        maxLines: 2,
                        hint: '≤ 300 chars',
                      ),
                      Row(
                        children: [
                          Expanded(
                            child: _buildTextField('seller_email', 'Email'),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _buildTextField('seller_phone', 'Phone'),
                          ),
                        ],
                      ),
                      Row(
                        children: [
                          Expanded(
                            child: _buildTextField(
                              'seller_gstin',
                              'GSTIN',
                              hint: '15-char GST number',
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _buildTextField(
                              'seller_pan',
                              'PAN',
                              hint: '10-char PAN',
                            ),
                          ),
                        ],
                      ),
                      ExpansionTile(
                        initiallyExpanded: false,
                        title: const Text('Banking details'),
                        childrenPadding: const EdgeInsets.symmetric(
                          horizontal: 5,
                          vertical: 8,
                        ),
                        children: [
                          _buildTextField(
                            'seller_bank_account_name',
                            'Account name',
                          ),
                          Row(
                            children: [
                              Expanded(
                                child: _buildTextField(
                                  'seller_bank_account_no',
                                  'Account number',
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: _buildTextField(
                                  'seller_bank_ifsc',
                                  'IFSC code',
                                ),
                              ),
                            ],
                          ),
                          _buildTextField(
                            'seller_bank_upi',
                            'UPI ID',
                            hint: 'id@psp',
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                _sectionTitle('BUYER BLOCK'),
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontFamily: 'Roboto',
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),

              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Column(
                    children: [
                      SizedBox(height: 10),
                      _buildTextField(
                        'buyer_name',
                        'Client name',
                        requiredField: true,
                        validator: (value) {
                          final trimmed = value?.trim() ?? '';
                          if (trimmed.isEmpty) return 'Client name is required';
                          if (trimmed.length < 2 || trimmed.length > 100) {
                            return 'Must be 2-100 characters';
                          }
                          return null;
                        },
                      ),
                      Row(
                        children: [
                          Expanded(
                            child: _buildTextField(
                              'buyer_email',
                              'Buyer email',
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _buildTextField(
                              'buyer_phone',
                              'Buyer phone',
                            ),
                          ),
                        ],
                      ),
                      _buildTextField(
                        'buyer_address',
                        'Buyer address',
                        maxLines: 2,
                      ),
                      _buildTextField('buyer_gstin', 'Buyer GSTIN'),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),
              Text(
                _sectionTitle('Document meta'),
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontFamily: 'Roboto',
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Column(
                    children: [
                      const SizedBox(height: 8),
                      _buildTextField(
                        'doc_no',
                        'Document number',
                        requiredField: _docType == 'TAX INVOICE',
                      ),
                      Row(
                        children: [
                          Expanded(
                            child: _buildTextField(
                              'ref_no',
                              'Reference / Quote title',
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _buildTextField('po_no', 'PO number'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: _buildTextField(
                              'issue_date',
                              'Issue date',
                              requiredField: true,
                              readOnly: true,
                              onTap: () =>
                                  _pickDate(_controllers['issue_date']!),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _buildTextField(
                              'due_date',
                              'Due date',
                              readOnly: true,
                              onTap: () => _pickDate(_controllers['due_date']!),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _buildTextField(
                              'valid_till',
                              'Valid till',
                              readOnly: true,
                              onTap: () =>
                                  _pickDate(_controllers['valid_till']!),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),
              Text(
                _sectionTitle('Items'),
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontFamily: 'Roboto',
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              ..._buildItemRows(),
              Align(
                alignment: Alignment.centerLeft,
                child: ElevatedButton.icon(
                  onPressed: _addItem,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue.shade800,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadiusGeometry.circular(10),
                    ),
                  ),
                  icon: const Icon(Icons.add, color: Colors.white),
                  label: Text(
                    'Add item',
                    style: TextStyle(
                      color: Colors.white,
                      fontFamily: 'Roboto',
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                _sectionTitle('Totals ($currency)'),
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontFamily: 'Roboto',
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Wrap(
                        spacing: 12,
                        runSpacing: 5,
                        children: [
                          Chip(
                            label: Text('Subtotal: ${totals['subtotal'] ?? 0}'),
                          ),
                          Chip(
                            label: Text(
                              'Discount: ${totals['discount_total'] ?? 0}',
                            ),
                          ),
                          Chip(label: Text('Tax: ${totals['tax_total'] ?? 0}')),
                          Chip(
                            label: Text(
                              'Grand total: ${totals['grand_total'] ?? 0}',
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      _buildTextField(
                        'totals_shipping',
                        'Shipping',
                        inputType: TextInputType.number,
                      ),
                      _buildTextField(
                        'totals_round_off',
                        'Round off',
                        inputType: TextInputType.number,
                        hint: _roundOffEnabled ? null : 'Round off disabled',
                      ),
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        value: _roundOffEnabled,
                        onChanged: (value) =>
                            setState(() => _roundOffEnabled = value),
                        title: Text(
                          'Apply nearest rupee round-off',
                          style: TextStyle(
                            color: Colors.black,
                            fontFamily: 'Roboto',
                            fontSize: 14,
                          ),
                        ),
                      ),

                      _buildTextField(
                        'totals_amount_in_words',
                        'Amount in words',
                        maxLines: 2,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                _sectionTitle('Payment'),
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontFamily: 'Roboto',
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Column(
                    children: [
                      Wrap(
                        spacing: 2,
                        children: [
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Radio<String>(
                                value: 'UPI',
                                groupValue: _paymentMode,
                                onChanged: (v) =>
                                    setState(() => _paymentMode = v!),
                              ),
                              const Text('UPI'),
                            ],
                          ),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Radio<String>(
                                value: 'Bank transfer',
                                groupValue: _paymentMode,
                                onChanged: (v) =>
                                    setState(() => _paymentMode = v!),
                              ),
                              const Text('Bank transfer'),
                            ],
                          ),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Radio<String>(
                                value: 'Other',
                                groupValue: _paymentMode,
                                onChanged: (v) =>
                                    setState(() => _paymentMode = v!),
                              ),
                              const Text('Other'),
                            ],
                          ),
                        ],
                      ),
                      SizedBox(height: 10),
                      _buildTextField('payment_upi', 'UPI ID'),
                      _buildTextField(
                        'payment_instructions',
                        'Payment instructions',
                        maxLines: 2,
                      ),
                      TextFormField(
                        controller: _controllers['payment_deeplink'],
                        readOnly: true,
                        decoration: InputDecoration(
                          labelText: 'UPI deeplink',
                          isDense: true,
                          contentPadding: EdgeInsets.symmetric(
                            vertical: 10,
                            horizontal: 12,
                          ),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade400,
                              width: 1,
                            ),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide(
                              color: Colors.grey.shade600,
                              width: 2,
                            ),
                          ),
                        ),
                      ),
                      SizedBox(height: 10),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          GestureDetector(
                            onTap: _generatePayLink,
                            child: Container(
                              width: MediaQuery.widthOf(context) * 0.5,
                              height: MediaQuery.heightOf(context) * 0.06,
                              decoration: BoxDecoration(
                                color: Colors.blue.shade800,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Center(
                                child: Text(
                                  'Generate Pay Link',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontFamily: 'Roboto',
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ),
                          ),

                          // ElevatedButton(
                          //   onPressed: _generatePayLink,
                          //
                          //   child: const Text('Generate Pay Link'),
                          // ),
                          GestureDetector(
                            onTap: _copyDeeplink,
                            child: Container(
                              width: MediaQuery.widthOf(context) * 0.35,
                              height: MediaQuery.heightOf(context) * 0.06,
                              decoration: BoxDecoration(
                                color: Colors.grey.shade50,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Center(
                                child: Text(
                                  'Copy Link',
                                  style: TextStyle(
                                    color: Colors.blue,
                                    fontFamily: 'Roboto',
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                _sectionTitle('Terms'),
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontFamily: 'Roboto',
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Column(
                    children: [
                      const SizedBox(height: 10),
                      _buildTextField('terms_title', 'Terms title'),
                      const SizedBox(height: 5),
                      _buildTextField(
                        'terms_bullets',
                        'Terms bullets (one per line)',
                        maxLines: 4,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                _sectionTitle('Notes'),
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontFamily: 'Roboto',
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Padding(
                  padding: const EdgeInsets.only(top: 12, left: 10, right: 10),
                  child: _buildTextField('notes', 'Notes', maxLines: 3),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                _sectionTitle('Branding'),
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontFamily: 'Roboto',
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Column(
                    children: [
                      const SizedBox(height: 10),
                      _buildTextField('branding_logo', 'Logo path'),
                      _buildTextField('branding_accent', 'Accent color (hex)'),
                      _buildTextField(
                        'branding_footer',
                        'Footer text',
                        maxLines: 2,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              if (_docType == 'QUOTATION') ...[
                Text(
                  _sectionTitle('Quotation options'),
                    style: TextStyle(
                      color: Colors.grey.shade600,
                      fontFamily: 'Roboto',
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                ),
                const SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10)
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: Column(
                      children: [
                        _buildTextField('quotation_title', 'Quote title'),
                        _buildTextField(
                          'quotation_validity_days',
                          'Validity days',
                          inputType: TextInputType.number,
                        ),
                        _buildTextField('quotation_offer_type', 'Offer type'),
                        SwitchListTile(
                          value: _pricingOptionsEnabled,
                          contentPadding: EdgeInsets.zero,
                          onChanged: (value) =>
                              setState(() => _pricingOptionsEnabled = value),
                          title: const Text('Enable pricing options (Option A/B/C)', style: TextStyle(
                            color: Colors.black,
                            fontFamily: 'Roboto',
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),),
                        ),
                        _buildTextField(
                          'quotation_advance_percent',
                          'Advance percent',
                          inputType: TextInputType.number,
                        ),
                        _buildTextField('quotation_delivery_window', 'Delivery window'),
                        _buildTextField(
                          'quotation_inclusions',
                          'Inclusions (one per line)',
                          maxLines: 3,
                        ),
                        _buildTextField(
                          'quotation_exclusions',
                          'Exclusions (one per line)',
                          maxLines: 3,
                        ),
                        _buildTextField(
                          'quotation_assumptions',
                          'Assumptions (one per line)',
                          maxLines: 3,
                        ),
                        _buildTextField('quotation_warranty', 'Warranty / Support'),
                        _buildTextField(
                          'quotation_change_rate',
                          'Change requests rate',
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
             ],

///////////////////////////////////////Tax invoice//////////////////////////
              if (_docType == 'TAX INVOICE') ...[
                Text(
                  _sectionTitle('Invoice specifics'),
                  style: TextStyle(
                    color: Colors.grey.shade600,
                    fontFamily: 'Roboto',
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: Column(
                      children: [
                        const SizedBox(height: 8),
                        _buildTextField(
                          'invoice_supply_date',
                          'Supply date',
                          readOnly: true,
                          onTap: () =>
                              _pickDate(_controllers['invoice_supply_date']!),
                        ),
                        SwitchListTile(
                          contentPadding: EdgeInsets.zero,
                          value: _billToShipSame,
                          onChanged: (value) =>
                              setState(() => _billToShipSame = value),
                          title: const Text(
                            'Bill-to and ship-to are the same',
                            style: TextStyle(
                              color: Colors.black,
                              fontFamily: 'Roboto',
                              fontSize: 14,
                            ),
                          ),
                        ),
                        if (!_billToShipSame)
                          _buildTextField(
                            'invoice_ship_to',
                            'Ship-to address',
                            maxLines: 2,
                          ),
                        _buildTextField(
                          'invoice_place_of_supply',
                          'Place of supply',
                          requiredField: true,
                        ),
                        SwitchListTile(
                          value: _reverseCharge,
                          contentPadding: EdgeInsets.zero,
                          onChanged: (value) =>
                              setState(() => _reverseCharge = value),
                          title: const Text(
                            'Reverse charge applicable',
                            style: TextStyle(
                              color: Colors.black,
                              fontFamily: 'Roboto',
                              fontSize: 14,
                            ),
                          ),
                        ),
                        _buildTextField('invoice_irn', 'E-invoice IRN'),
                        Row(
                          children: [
                            Expanded(
                              child: _buildTextField(
                                'invoice_ack_no',
                                'Ack no.',
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: _buildTextField(
                                'invoice_ack_date',
                                'Ack date',
                                readOnly: true,
                                onTap: () => _pickDate(
                                  _controllers['invoice_ack_date']!,
                                ),
                              ),
                            ),
                          ],
                        ),
                        Row(
                          children: [
                            Expanded(
                              child: _buildTextField(
                                'invoice_tcs_percent',
                                'TCS %',
                                inputType: TextInputType.number,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: _buildTextField(
                                'invoice_tds_note',
                                'TDS note',
                                maxLines: 2,
                              ),
                            ),
                          ],
                        ),
                        _buildTextField(
                          'invoice_transport',
                          'Transport details',
                        ),
                        SwitchListTile(
                          value: _roundOffEnabled,
                          contentPadding: EdgeInsets.zero,
                          onChanged: (value) =>
                              setState(() => _roundOffEnabled = value),
                          title: const Text(
                            'Round off on grand total',
                            style: TextStyle(
                              color: Colors.black,
                              fontFamily: 'Roboto',
                              fontSize: 14,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 24),
              ],

//////////////////////////////////project brief///////////////////////////////////////

              if (_docType == 'PROJECT BRIEF') ...[
                Text(
                  _sectionTitle('Project brief header'),
    style: TextStyle(
    color: Colors.grey.shade600,
    fontFamily: 'Roboto',
    fontSize: 14,
    fontWeight: FontWeight.w600,
    ),
                ),
              const SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10)
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: Column(
                      children: [
                        _buildTextField(
                          'brief_title',
                          'Project title',
                          requiredField: true,
                        ),
                        _buildTextField(
                          'brief_objective',
                          'Objective',
                          maxLines: 3,
                          requiredField: true,
                        ),
                        _buildTextField(
                          'brief_success_metrics',
                          'Success metrics (one per line)',
                          maxLines: 3,
                        ),
                        _buildTextField(
                          'brief_scope',
                          'In scope (one per line)',
                          maxLines: 3,
                          requiredField: true,
                        ),
                        _buildTextField(
                          'brief_out_scope',
                          'Out of scope (one per line)',
                          maxLines: 3,
                        ),
                        _buildTextField(
                          'brief_deliverables',
                          'Deliverables (one per line)',
                          maxLines: 3,
                          requiredField: true,
                        ),
                        _buildTextField(
                          'brief_assumptions',
                          'Assumptions (one per line)',
                          maxLines: 3,
                        ),
                        const SizedBox(height: 16),

                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 20),
              Text(
                _sectionTitle('Milestones'),
    style: TextStyle(
    color: Colors.grey.shade600,
    fontFamily: 'Roboto',
    fontSize: 14,
    fontWeight: FontWeight.w600,
    ),
              ),
              const SizedBox(height: 12),
                Column(
                  children: [

                    ..._buildMilestoneRows(),
                    const SizedBox(height: 5),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: ElevatedButton.icon(
                        onPressed: _addMilestone,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue.shade800,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadiusGeometry.circular(10),
                          ),
                        ),
                        icon: const Icon(Icons.add, color: Colors.white),
                        label: Text(
                          'Add Milestone',
                          style: TextStyle(
                            color: Colors.white,
                            fontFamily: 'Roboto',
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _sectionTitle('Billing plan'),
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontFamily: 'Roboto',
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Container(
                      decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(10)
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(8.0),
                        child: Column(
                          children: [
                            ..._buildBillingRows(),
                            Align(
                              alignment: Alignment.centerLeft,
                              child: ElevatedButton.icon(
                                onPressed: _addBillingPart,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.blue.shade800,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadiusGeometry.circular(10),
                                  ),
                                ),
                                icon: const Icon(Icons.add, color: Colors.white),
                                label: Text(
                                  'Add billing part',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontFamily: 'Roboto',
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 8),
                            _buildTextField(
                              'brief_timeline_days',
                              'Timeline days',
                              inputType: TextInputType.number,
                              requiredField: true,
                            ),
                            _buildTextField(
                              'brief_risks',
                              'Risks (one per line)',
                              maxLines: 3,
                            ),
                            _buildTextField('brief_communication', 'Communication cadence'),
                            _buildTextField('brief_change_control', 'Change control'),
                            _buildTextField(
                              'brief_acceptance',
                              'Acceptance criteria (one per line)',
                              maxLines: 3,
                            ),
                            _buildTextField('brief_support_window', 'Support window'),
                          ],
                        ),
                      ),
                    )

                  ],
                ),

                const SizedBox(height: 24),
              ],
              ExpansionTile(
                backgroundColor: Colors.white,
                collapsedBackgroundColor: Colors.white,
                title: const Text(
                  'Advanced settings',
                  style: TextStyle(
                    color: Colors.black,
                    fontFamily: 'Roboto',
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                childrenPadding: const EdgeInsets.all(12),
                children: [
                  SwitchListTile(
                    value: _discountAmountOnly,
                    onChanged: (value) =>
                        setState(() => _discountAmountOnly = value),
                    title: const Text(
                      'Discount mode: per-line amount only',
                      style: TextStyle(
                        color: Colors.black,
                        fontFamily: 'Roboto',
                        fontSize: 14,
                      ),
                    ),
                  ),
                  ListTile(
                    title: Text(
                      'Branding options',
                      style: TextStyle(
                        color: Colors.black,
                        fontFamily: 'Roboto',
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    subtitle: const Text(
                      'Logo, accent color, footer text available above.',
                      style: TextStyle(
                        color: Colors.black,
                        fontFamily: 'Roboto',
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 96),
            ],
          ),
        ),
      ),
      bottomNavigationBar: SafeArea(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              Expanded(
                child: GestureDetector(
                  onTap: _exportPdf,
                  child: Container(
                    width: double.infinity,
                    height: MediaQuery.heightOf(context) * 0.06,
                    decoration: BoxDecoration(
                      color: Colors.blue.shade800,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Center(
                      child: Text(
                        "Export PDF",
                        style: TextStyle(
                          color: Colors.white,
                          fontFamily: 'Roboto',
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                ),
              ),

              const SizedBox(width: 12),
              Expanded(
                child: GestureDetector(
                  onTap: _share,
                  child: Container(
                    width: double.infinity,
                    height: MediaQuery.heightOf(context) * 0.06,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Center(
                      child: Text(
                        "Share",
                        style: TextStyle(
                          color: Colors.blue.shade800,
                          fontFamily: 'Roboto',
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
