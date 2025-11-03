import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:intl/intl.dart';
import 'package:http/http.dart' as http;

import 'client_scr.dart';
import 'editor_screen.dart';
import 'history_screen.dart';
import 'seller_settings_scr.dart';

class HomeDraft extends StatefulWidget {
  const HomeDraft({super.key});

  @override
  State<HomeDraft> createState() => _HomeDraftState();
}

class _HomeDraftState extends State<HomeDraft> {
  final TextEditingController _desc = TextEditingController();
  late final TextEditingController _workspaceCtrl;
  late final TextEditingController _localeCtrl;
  late final TextEditingController _apiBaseUrlCtrl;
  late final TextEditingController _apiKeyCtrl;
  late final TextEditingController _providerCtrl;
  late final TextEditingController _modelCtrl;

  final List<String> _currencies = const ['INR', 'USD', 'EUR', 'GBP', 'AUD', 'CAD'];
  final Box _settingsBox = Hive.box('settings');

  String _selectedDoc = 'Quotation';
  String _currency = 'INR';
  bool _loading = false;
  String? _selectedClientId;

  bool get _canGenerate =>
      !_loading && _desc.text.trim().length >= 10;

  @override
  void initState() {
    super.initState();
    _workspaceCtrl = TextEditingController(
      text: _settingsBox.get('workspace_id', defaultValue: 'default')?.toString() ?? 'default',
    );
    _localeCtrl = TextEditingController(
      text: _settingsBox.get('locale', defaultValue: 'en-IN')?.toString() ?? 'en-IN',
    );
    _apiBaseUrlCtrl = TextEditingController(
      text: _settingsBox.get('api_base_url', defaultValue: 'http://localhost:8000')?.toString() ??
          'http://localhost:8000',
    );
    _apiKeyCtrl = TextEditingController(
      text: _settingsBox.get('api_key', defaultValue: '')?.toString() ?? '',
    );
    _providerCtrl = TextEditingController(
      text: _settingsBox.get('provider_override', defaultValue: '')?.toString() ?? '',
    );
    _modelCtrl = TextEditingController(
      text: _settingsBox.get('model_override', defaultValue: '')?.toString() ?? '',
    );

    final clients = _readClients();
    if (clients.isNotEmpty) {
      _selectedClientId = clients.first['id']?.toString();
    }
  }

  @override
  void dispose() {
    _desc.dispose();
    _workspaceCtrl.dispose();
    _localeCtrl.dispose();
    _apiBaseUrlCtrl.dispose();
    _apiKeyCtrl.dispose();
    _providerCtrl.dispose();
    _modelCtrl.dispose();
    super.dispose();
  }

  Map<String, dynamic> _readSeller({Box? source}) {
    final box = source ?? _settingsBox;
    final seller = box.get('seller', defaultValue: <String, dynamic>{});
    if (seller is Map) {
      return jsonDecode(jsonEncode(seller)) as Map<String, dynamic>;
    }
    return <String, dynamic>{};
  }

  List<Map<String, dynamic>> _readClients() {
    return _normalizeClients(_settingsBox);
  }

  List<Map<String, dynamic>> _normalizeClients(Box box) {
    final stored = box.get('clients', defaultValue: <Map<String, dynamic>>[]);
    if (stored is! List) {
      return <Map<String, dynamic>>[];
    }

    final sanitized = <Map<String, dynamic>>[];
    final updated = <Map<String, dynamic>>[];
    var mutated = false;

    for (var index = 0; index < stored.length; index++) {
      final entry = stored[index];
      if (entry is! Map) {
        continue;
      }

      final client = Map<String, dynamic>.from(entry as Map);
      if (!_hasClientId(client)) {
        client['id'] = _generateClientId(client, index);
        mutated = true;
      }

      updated.add(client);
      sanitized.add(jsonDecode(jsonEncode(client)) as Map<String, dynamic>);
    }

    if (mutated) {
      box.put('clients', updated);
    }

    return sanitized;
  }

  bool _hasClientId(Map<String, dynamic> client) {
    final id = client['id'];
    return id != null && id.toString().trim().isNotEmpty;
  }

  String _generateClientId(Map<String, dynamic> client, int index) {
    final email = client['email']?.toString().trim();
    if (email != null && email.isNotEmpty) {
      return 'client-${email.toLowerCase()}';
    }

    final phone = client['phone']?.toString().trim();
    if (phone != null && phone.isNotEmpty) {
      return 'client-$phone';
    }

    final name = client['name']?.toString().trim();
    if (name != null && name.isNotEmpty) {
      final slug = name
          .toLowerCase()
          .replaceAll(RegExp(r'[^a-z0-9]+'), '-')
          .replaceAll(RegExp(r'-+'), '-')
          .replaceAll(RegExp(r'^-+'), '')
          .replaceAll(RegExp(r'-+$'), '');
      if (slug.isNotEmpty) {
        return 'client-$slug-$index';
      }
    }

    return 'client-${DateTime.now().microsecondsSinceEpoch}-$index';
  }

  Future<void> _generateDraft() async {
    if (!_canGenerate) return;

    final seller = _readSeller();
    final clients = _readClients();
    final client = clients.firstWhere(
      (element) => element['id']?.toString() == _selectedClientId,
      orElse: () => <String, dynamic>{},
    );

    if (seller.isEmpty || (seller['name']?.toString().isEmpty ?? true)) {
      _showError('Add your business information before generating documents.');
      return;
    }
    if (client.isEmpty) {
      _showError('Add at least one client and select it before generating.');
      return;
    }
    if (_apiBaseUrlCtrl.text.trim().isEmpty) {
      _showError('Enter an API base URL (e.g., http://localhost:8000).');
      return;
    }

    final payload = _buildRequestPayload(seller, client);
    final endpoint = _endpointForSelection();
    final uri = _resolveEndpoint(endpoint);
    final headers = _buildHeaders();

    setState(() => _loading = true);
    try {
      final response = await http.post(
        uri,
        headers: headers,
        body: jsonEncode(payload),
      );

      if (response.statusCode != 200) {
        final message = _extractError(response.body);
        _showError('Generation failed: ${response.statusCode} $message');
        return;
      }
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final normalized = _normalizeBundle(data, seller, client);
      normalized['source_request'] = payload;
      normalized['workspace_id'] = headers['X-Workspace-Id'];

      final box = Hive.box('drafts');
      await box.add({
        'status': 'generated',
        'bundle': normalized,
        'created': DateTime.now().toIso8601String(),
        'endpoint': endpoint,
      });

      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => EditorScreen(initialBundle: normalized),
        ),
      );
    } catch (error) {
      _showError('Unable to reach API: $error');
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Map<String, String> _buildHeaders() {
    final workspace = _workspaceCtrl.text.trim().isEmpty
        ? 'default'
        : _workspaceCtrl.text.trim();
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'X-Workspace-Id': workspace,
    };
    if (_providerCtrl.text.trim().isNotEmpty) {
      headers['X-Provider'] = _providerCtrl.text.trim();
    }
    if (_modelCtrl.text.trim().isNotEmpty) {
      headers['X-Model'] = _modelCtrl.text.trim();
    }
    if (_apiKeyCtrl.text.trim().isNotEmpty) {
      headers['x-api-key'] = _apiKeyCtrl.text.trim();
    }
    return headers;
  }

  String _endpointForSelection() {
    switch (_selectedDoc) {
      case 'Tax Invoice':
        return '/v1/generate/invoice';
      case 'Project Brief':
        return '/v1/generate/project-brief';
      default:
        return '/v1/generate/quotation';
    }
  }

  Uri _resolveEndpoint(String path) {
    var base = _apiBaseUrlCtrl.text.trim();
    if (base.endsWith('/')) {
      base = base.substring(0, base.length - 1);
    }
    return Uri.parse('$base$path');
  }

  Map<String, dynamic> _buildRequestPayload(
    Map<String, dynamic> seller,
    Map<String, dynamic> client,
  ) {
    final locale = _localeCtrl.text.trim().isEmpty
        ? 'en-IN'
        : _localeCtrl.text.trim();
    final requirement = _desc.text.trim();

    final now = DateTime.now();
    final dateFormat = DateFormat('yyyy-MM-dd');

    final hints = {
      'doc_meta': {
        'doc_no': '',
        'po_no': '',
        'ref_no': '',
      },
      'dates': {
        'issue_date': dateFormat.format(now),
        'due_date': dateFormat.format(now.add(const Duration(days: 7))),
        'valid_till': dateFormat.format(now.add(const Duration(days: 14))),
      },
      'items': [
        {
          'description': 'Line item from requirement',
          'hsn_sac': '',
          'qty': 1,
          'unit': 'job',
          'unit_price': 0,
          'discount': 0,
          'tax_rate': 0,
        },
      ],
      'terms': {
        'title': 'Terms & Conditions',
        'bullets': [
          'Update these terms after AI draft is ready.',
        ],
      },
      'payment': {
        'mode': 'UPI',
        'instructions': 'Payment instructions will be updated post-generation.',
        'upi_deeplink': '',
      },
    };

    if (_selectedDoc == 'Tax Invoice') {
      hints['payment'] = {
        'mode': 'BANK_TRANSFER',
        'instructions': 'Bank transfer preferred.',
        'upi_deeplink': '',
      };
    }

    return {
      'from': seller,
      'to': client,
      'currency': _currency,
      'locale': locale,
      'requirement': requirement,
      'hints': hints,
      'workspace_id': _workspaceCtrl.text.trim().isEmpty
          ? 'default'
          : _workspaceCtrl.text.trim(),
    };
  }

  Map<String, dynamic> _normalizeBundle(
    Map<String, dynamic> bundle,
    Map<String, dynamic> seller,
    Map<String, dynamic> client,
  ) {
    final docType = _selectedDoc == 'Tax Invoice'
        ? 'TAX INVOICE'
        : _selectedDoc.toUpperCase();
    bundle['doc_type'] = bundle['doc_type'] ?? docType;
    if (bundle['doc_type'] == 'TAX_INVOICE') {
      bundle['doc_type'] = 'TAX INVOICE';
    }
    bundle['currency'] ??= _currency;
    bundle['locale'] ??= _localeCtrl.text.trim().isEmpty
        ? 'en-IN'
        : _localeCtrl.text.trim();
    bundle['seller'] ??= {};
    bundle['buyer'] ??= {};
    bundle['doc_meta'] ??= {};
    bundle['dates'] ??= {};
    bundle['items'] ??= [];
    bundle['totals'] ??= {
      'subtotal': 0,
      'discount_total': 0,
      'tax_total': 0,
      'shipping': 0,
      'round_off': 0,
      'grand_total': 0,
      'amount_in_words': '',
    };
    bundle['terms'] ??= {
      'title': 'Terms & Conditions',
      'bullets': <String>[],
    };
    bundle['payment'] ??= {};
    bundle['branding'] ??= seller['branding'] ?? {};
    bundle['notes'] ??= '';

    if ((bundle['seller'] as Map).isEmpty) {
      bundle['seller'] = _summarizeParty(seller);
    }
    if ((bundle['buyer'] as Map).isEmpty) {
      bundle['buyer'] = _summarizeParty(client);
    }

    if (_selectedDoc == 'Project Brief' && bundle['project_brief'] == null) {
      bundle['project_brief'] = {
        'title': 'Project brief',
        'objective': '',
        'scope': <String>[],
        'deliverables': <String>[],
        'assumptions': <String>[],
        'milestones': <Map<String, dynamic>>[],
        'timeline_days': 0,
        'billing_plan': <Map<String, dynamic>>[],
        'risks': <String>[],
        'seller': _summarizeParty(seller),
        'buyer': _summarizeParty(client),
      };
    }
    return bundle;
  }

  Map<String, String> _summarizeParty(Map<String, dynamic> party) {
    final address = _formatAddress(
      Map<String, dynamic>.from(
        party['billing_address'] as Map? ?? <String, dynamic>{},
      ),
    );
    return {
      'name': party['name']?.toString() ?? '',
      'address': address,
      'email': party['email']?.toString() ?? '',
      'phone': party['phone']?.toString() ?? '',
      'gstin': party['gstin']?.toString() ?? '',
      'pan': party['pan']?.toString() ?? '',
    };
  }

  String _formatAddress(Map<String, dynamic> address) {
    final parts = [
      address['line1'],
      address['line2'],
      address['city'],
      address['state'],
      address['postal_code'],
      address['country'],
    ]
        .where((element) => element != null && element.toString().trim().isNotEmpty)
        .map((e) => e.toString().trim())
        .toList();
    return parts.join(', ');
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  String _extractError(String body) {
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map && decoded['detail'] != null) {
        return decoded['detail'].toString();
      }
      return body;
    } catch (_) {
      return body;
    }
  }

  void _persistSetting(String key, String value) {
    _settingsBox.put(key, value);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text(
          'Create Invoice',
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
              colors: <Color>[
                Colors.blue.shade800,
                Colors.blue.shade900,
              ],
            ),
          ),
        ),
        centerTitle: true,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: Column(
        children: [
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(height: MediaQuery.sizeOf(context).height * 0.01),
                    Text(
                      'INVOICE TYPE',
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontFamily: 'Roboto',
                        fontSize: 12,
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
                    const SizedBox(height: 20),
                    ValueListenableBuilder<Box>(
                      valueListenable: _settingsBox.listenable(keys: ['seller', 'clients']),
                      builder: (context, box, _) {
                        final seller = _readSeller(source: box);
                        final clients = _normalizeClients(box);
                        if (clients.isEmpty && _selectedClientId != null) {
                          WidgetsBinding.instance.addPostFrameCallback((_) {
                            if (mounted) {
                              setState(() => _selectedClientId = null);
                            }
                          });
                        } else if (clients.isNotEmpty &&
                            (clients.every((c) => c['id']?.toString() != _selectedClientId) ||
                                _selectedClientId == null)) {
                          WidgetsBinding.instance.addPostFrameCallback((_) {
                            if (mounted) {
                              setState(() => _selectedClientId = clients.first['id']?.toString());
                            }
                          });
                        }
                        final selectedClient = clients.firstWhere(
                          (c) => c['id']?.toString() == _selectedClientId,
                          orElse: () => <String, dynamic>{},
                        );
                        return _businessInfoCard(seller, clients, selectedClient);
                      },
                    ),
                    const SizedBox(height: 20),
                    _configurationCard(),
                    const SizedBox(height: 20),
                    Text(
                      'WORK REQUIREMENT',
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontFamily: 'Roboto',
                        fontSize: 12,
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
                        child: TextField(
                          controller: _desc,
                          maxLines: 5,
                          onChanged: (_) => setState(() {}),
                          decoration: InputDecoration(
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
                              borderSide: BorderSide(color: Colors.grey.shade400, width: 0.5),
                            ),
                            hintStyle: TextStyle(
                              color: Colors.grey.shade600,
                              fontFamily: 'Roboto',
                              fontSize: 12,
                            ),
                            hintText:
                                'Describe the work requirement. Include deliverables, timelines, budget hints, and any must-have features.',
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          Container(
            color: Colors.white,
            width: double.infinity,
            height: MediaQuery.sizeOf(context).height * 0.08,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: Row(
                children: [
                  Expanded(
                    child: SizedBox(
                      height: MediaQuery.sizeOf(context).height * 0.06,
                      child: ElevatedButton(
                        onPressed: _canGenerate ? _generateDraft : null,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue.shade800,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                        child: _loading
                            ? const CircularProgressIndicator.adaptive()
                            : Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: const [
                                  Icon(
                                    Icons.drafts,
                                    color: Colors.white,
                                  ),
                                  SizedBox(width: 5),
                                  Text(
                                    'Generate Draft',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontFamily: 'Roboto',
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
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
                      width: MediaQuery.sizeOf(context).width * 0.4,
                      height: MediaQuery.sizeOf(context).height * 0.06,
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.history_outlined,
                            color: Colors.blue.shade800,
                          ),
                          const SizedBox(width: 5),
                          Text(
                            'History',
                            style: TextStyle(
                              color: Colors.blue.shade800,
                              fontFamily: 'Roboto',
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
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
              Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                  fontFamily: 'Roboto',
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

  Widget _businessInfoCard(
    Map<String, dynamic> seller,
    List<Map<String, dynamic>> clients,
    Map<String, dynamic> selectedClient,
  ) {
    final sellerName = seller['name']?.toString() ?? '';
    final sellerSubtitle = _formatPartySubtitle(seller);
    final clientName = selectedClient['name']?.toString() ?? '';
    final clientSubtitle = _formatPartySubtitle(selectedClient);

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'BUSINESS INFO',
              style: TextStyle(
                color: Colors.grey.shade600,
                fontFamily: 'Roboto',
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            ListTile(
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const SellerSettings()),
              ),
              leading: CircleAvatar(
                backgroundColor: Colors.blue.shade100,
                child: Icon(Icons.perm_identity, color: Colors.blue.shade600),
              ),
              title: Text(
                sellerName.isEmpty ? 'Add business information' : sellerName,
                style: const TextStyle(
                  fontFamily: 'Roboto',
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              subtitle: sellerSubtitle.isEmpty ? null : Text(sellerSubtitle),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            ),
            const Divider(),
            ListTile(
              title: DropdownButtonFormField<String>(
                value: _selectedClientId,
                items: clients
                    .map(
                      (client) => DropdownMenuItem(
                        value: client['id']?.toString(),
                        child: Text(
                          client['name']?.toString().isEmpty ?? true
                              ? 'Unnamed client'
                              : client['name'].toString(),
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) => setState(() => _selectedClientId = value),
                decoration: InputDecoration(
                  labelText: clients.isEmpty ? 'Add a client to continue' : 'Select client',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: BorderSide(color: Colors.grey.shade400, width: 0.8),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: BorderSide(color: Colors.grey.shade400, width: 0.8),
                  ),
                ),
              ),
              subtitle: clientSubtitle.isEmpty ? null : Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(clientSubtitle),
              ),
              trailing: IconButton(
                icon: const Icon(Icons.open_in_new),
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const ClientsScreen()),
                ),
              ),
            ),
            const Divider(),
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: Colors.green.shade100,
                  child: Icon(Icons.account_balance_wallet_outlined, color: Colors.green.shade600),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _currency,
                    items: _currencies
                        .map(
                          (c) => DropdownMenuItem(
                            value: c,
                            child: Text(
                              c,
                              style: const TextStyle(
                                color: Colors.black,
                                fontFamily: 'Roboto',
                                fontSize: 14,
                              ),
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: (v) => setState(() => _currency = v ?? 'INR'),
                    decoration: InputDecoration(
                      labelText: 'Choose Currency',
                      labelStyle: TextStyle(
                        color: Colors.grey[600],
                        fontFamily: 'Roboto',
                        fontSize: 16,
                      ),
                      border: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.grey.shade600, width: 0.5),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.grey.shade400, width: 0.8),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.grey.shade400, width: 1.2),
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _configurationCard() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'API CONFIGURATION',
              style: TextStyle(
                color: Colors.grey.shade600,
                fontFamily: 'Roboto',
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            _settingsField(
              controller: _workspaceCtrl,
              label: 'Workspace ID',
              keyName: 'workspace_id',
            ),
            _settingsField(
              controller: _localeCtrl,
              label: 'Locale',
              keyName: 'locale',
            ),
            _settingsField(
              controller: _apiBaseUrlCtrl,
              label: 'API Base URL',
              keyName: 'api_base_url',
              hint: 'http://localhost:8000',
            ),
            _settingsField(
              controller: _apiKeyCtrl,
              label: 'x-api-key (optional)',
              keyName: 'api_key',
              obscure: true,
            ),
            _settingsField(
              controller: _providerCtrl,
              label: 'X-Provider override (optional)',
              keyName: 'provider_override',
            ),
            _settingsField(
              controller: _modelCtrl,
              label: 'X-Model override (optional)',
              keyName: 'model_override',
            ),
          ],
        ),
      ),
    );
  }

  Widget _settingsField({
    required TextEditingController controller,
    required String label,
    required String keyName,
    String? hint,
    bool obscure = false,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: controller,
        obscureText: obscure,
        onChanged: (value) => _persistSetting(keyName, value.trim()),
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade600, width: 0.5),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade400, width: 0.8),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade400, width: 1.2),
          ),
        ),
      ),
    );
  }

  String _formatPartySubtitle(Map<String, dynamic> party) {
    if (party.isEmpty) return '';
    final parts = <String>[];
    if ((party['contact_person']?.toString() ?? '').isNotEmpty) {
      parts.add(party['contact_person'].toString());
    }
    if ((party['email']?.toString() ?? '').isNotEmpty) {
      parts.add(party['email'].toString());
    }
    if ((party['phone']?.toString() ?? '').isNotEmpty) {
      parts.add(party['phone'].toString());
    }
    if (parts.isEmpty) {
      return _formatAddress(
        Map<String, dynamic>.from(
          party['billing_address'] as Map? ?? <String, dynamic>{},
        ),
      );
    }
    return parts.join(' • ');
  }
}
