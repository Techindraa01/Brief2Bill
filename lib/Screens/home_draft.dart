import 'dart:convert';
import 'dart:math';

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

    final clients = _readClients();
    if (clients.isNotEmpty) {
      _selectedClientId = clients.first['id']?.toString();
    }
  }

  @override
  void dispose() {
    _desc.dispose();
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

  String _settingWithDefault(String key, String fallback) {
    final value = _settingsBox.get(key);
    if (value == null) {
      return fallback;
    }
    final trimmed = value.toString().trim();
    return trimmed.isEmpty ? fallback : trimmed;
  }

  String get _workspaceId => _settingWithDefault('workspace_id', 'default');

  String get _locale => _settingWithDefault('locale', 'en-IN');

  String get _apiBaseUrl => _settingWithDefault('api_base_url', 'http://localhost:8000');

  String get _apiKey => _settingWithDefault('api_key', '');

  String get _providerOverride => _settingWithDefault('provider_override', '');

  String get _modelOverride => _settingWithDefault('model_override', '');

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
      _showError('Add your "From" details before generating documents.');
      return;
    }
    if (client.isEmpty) {
      _showError('Add at least one "To" contact and select it before generating.');
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
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'X-Workspace-Id': _workspaceId,
    };
    final provider = _providerOverride;
    if (provider.isNotEmpty) {
      headers['X-Provider'] = provider;
    }
    final model = _modelOverride;
    if (model.isNotEmpty) {
      headers['X-Model'] = model;
    }
    final apiKey = _apiKey;
    if (apiKey.isNotEmpty) {
      headers['x-api-key'] = apiKey;
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
    var base = _apiBaseUrl;
    if (base.endsWith('/')) {
      base = base.substring(0, base.length - 1);
    }
    return Uri.parse('$base$path');
  }

  Map<String, dynamic> _buildRequestPayload(
    Map<String, dynamic> seller,
    Map<String, dynamic> client,
  ) {
    final locale = _locale;
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
      'workspace_id': _workspaceId,
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
    bundle['locale'] ??= _locale;
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
              'FROM',
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
                sellerName.isEmpty ? 'Add From details' : sellerName,
                style: const TextStyle(
                  fontFamily: 'Roboto',
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              subtitle: sellerSubtitle.isEmpty
                  ? const Text('Tap to update your "From" information.')
                  : Text(sellerSubtitle),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            ),
            const Divider(),
            Text(
              'TO',
              style: TextStyle(
                color: Colors.grey.shade600,
                fontFamily: 'Roboto',
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            ListTile(
              onTap: () => _showClientPicker(clients),
              leading: CircleAvatar(
                backgroundColor: Colors.orange.shade100,
                child: Icon(Icons.person_outline, color: Colors.orange.shade600),
              ),
              title: Text(
                _selectedClientTitle(selectedClient, clients.isEmpty),
                style: const TextStyle(
                  fontFamily: 'Roboto',
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              subtitle: Text(
                clientSubtitle.isNotEmpty
                    ? clientSubtitle
                    : clients.isEmpty
                        ? 'Add a "To" contact to continue.'
                        : 'Tap to choose from saved clients.',
              ),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            ),
            const Divider(),
            const SizedBox(height: 8),
            Text(
              'CURRENCY',
              style: TextStyle(
                color: Colors.grey.shade600,
                fontFamily: 'Roboto',
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            DecoratedBox(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.shade100),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.04),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _currency,
                    isExpanded: true,
                    borderRadius: BorderRadius.circular(12),
                    icon: Icon(
                      Icons.keyboard_arrow_down_rounded,
                      color: Colors.blue.shade600,
                    ),
                    dropdownColor: Colors.white,
                    style: const TextStyle(
                      fontFamily: 'Roboto',
                      fontSize: 16,
                      color: Colors.black87,
                    ),
                    items: _currencies
                        .map(
                          (c) => DropdownMenuItem(
                            value: c,
                            child: Row(
                              children: [
                                CircleAvatar(
                                  radius: 16,
                                  backgroundColor: Colors.blue.shade50,
                                  child: Icon(
                                    Icons.currency_exchange,
                                    color: Colors.blue.shade600,
                                    size: 18,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Text(c),
                              ],
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: (value) {
                      if (value == null) return;
                      setState(() => _currency = value);
                    },
                  ),
                ),
              ),
            ),
          ],
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

  String _selectedClientTitle(
    Map<String, dynamic> selectedClient,
    bool noClients,
  ) {
    if (selectedClient.isNotEmpty) {
      final name = selectedClient['name']?.toString().trim() ?? '';
      if (name.isNotEmpty) {
        return name;
      }
      if ((selectedClient['contact_person']?.toString().trim() ?? '').isNotEmpty) {
        return selectedClient['contact_person'].toString();
      }
      return 'Saved contact';
    }
    return noClients ? 'Add To details' : 'Choose a "To" contact';
  }

  Future<void> _showClientPicker(List<Map<String, dynamic>> clients) async {
    final result = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) {
        final sheetContent = clients.isEmpty
            ? _EmptyClientSheet(onAddNew: () => Navigator.pop(context, 'add_new'))
            : _ClientPickerSheet(
                clients: clients,
                selectedClientId: _selectedClientId,
                formatSubtitle: _formatPartySubtitle,
                onSelect: (id) => Navigator.pop(context, id),
                onAddNew: () => Navigator.pop(context, 'add_new'),
              );

        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: SafeArea(top: false, child: sheetContent),
        );
      },
    );

    if (!mounted || result == null) return;

    if (result == 'add_new') {
      await Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => const ClientsScreen()),
      );
      return;
    }

    setState(() => _selectedClientId = result);
  }
}

class _EmptyClientSheet extends StatelessWidget {
  const _EmptyClientSheet({required this.onAddNew});

  final VoidCallback onAddNew;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 28, 20, 28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'No saved clients yet',
            style: TextStyle(
              fontFamily: 'Roboto',
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Add your first "To" contact to reuse it across documents.',
            style: TextStyle(
              fontFamily: 'Roboto',
              fontSize: 14,
              color: Colors.grey.shade700,
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              icon: const Icon(Icons.add),
              label: const Text('Add new "To" contact'),
              onPressed: onAddNew,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue.shade600,
                foregroundColor: Colors.white,
                textStyle: const TextStyle(
                  fontFamily: 'Roboto',
                  fontWeight: FontWeight.w600,
                ),
                minimumSize: const Size.fromHeight(48),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ClientPickerSheet extends StatelessWidget {
  const _ClientPickerSheet({
    required this.clients,
    required this.selectedClientId,
    required this.formatSubtitle,
    required this.onSelect,
    required this.onAddNew,
  });

  final List<Map<String, dynamic>> clients;
  final String? selectedClientId;
  final String Function(Map<String, dynamic>) formatSubtitle;
  final ValueChanged<String> onSelect;
  final VoidCallback onAddNew;

  @override
  Widget build(BuildContext context) {
    final height = min(MediaQuery.of(context).size.height * 0.7, 440.0);
    return SizedBox(
      height: height,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 28, 20, 12),
            child: Row(
              children: [
                const Expanded(
                  child: Text(
                    'Select "To" contact',
                    style: TextStyle(
                      fontFamily: 'Roboto',
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                TextButton.icon(
                  onPressed: onAddNew,
                  icon: const Icon(Icons.add_circle_outline),
                  label: const Text('Add new'),
                  style: TextButton.styleFrom(
                    foregroundColor: Colors.blue.shade600,
                    textStyle: const TextStyle(
                      fontFamily: 'Roboto',
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListView.separated(
              itemCount: clients.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final client = clients[index];
                final id = client['id']?.toString();
                final title = client['name']?.toString().trim();
                final subtitle = formatSubtitle(client);
                final isSelected = id == selectedClientId;
                return ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Colors.orange.shade100,
                    child: Icon(
                      isSelected ? Icons.check_circle : Icons.person_outline,
                      color: Colors.orange.shade600,
                    ),
                  ),
                  title: Text(
                    (title == null || title.isEmpty) ? 'Unnamed contact' : title,
                    style: const TextStyle(
                      fontFamily: 'Roboto',
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  subtitle: subtitle.isEmpty
                      ? null
                      : Text(
                          subtitle,
                          style: TextStyle(
                            color: Colors.grey.shade600,
                            fontFamily: 'Roboto',
                          ),
                        ),
                  onTap: id == null ? null : () => onSelect(id),
                );
              },
            ),
          ),
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onAddNew,
                icon: const Icon(Icons.add),
                label: const Text('Add new "To" contact'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue.shade600,
                  foregroundColor: Colors.white,
                  textStyle: const TextStyle(
                    fontFamily: 'Roboto',
                    fontWeight: FontWeight.w600,
                  ),
                  minimumSize: const Size.fromHeight(50),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
