import 'package:flutter/material.dart';
import 'package:hive/hive.dart';

import '../Utils/form_groups.dart';
import '../Utils/reusables.dart';

class ClientsScreen extends StatefulWidget {
  const ClientsScreen({super.key});

  @override
  State<ClientsScreen> createState() => _ClientsScreenState();
}

class _ClientsScreenState extends State<ClientsScreen> {
  final _box = Hive.box('settings');
  final _name = TextEditingController();
  final _contactPerson = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _website = TextEditingController();
  final _gstin = TextEditingController();
  final _pan = TextEditingController();
  final _notes = TextEditingController();
  final _placeOfSupply = TextEditingController();

  final AddressControllers _billingAddress = AddressControllers();
  final AddressControllers _shippingAddress = AddressControllers();

  bool _shipSameAsBilling = true;
  int? _editingIndex;
  List<Map<String, dynamic>> clients = [];

  @override
  void initState() {
    super.initState();
    clients = _readClients();
  }

  List<Map<String, dynamic>> _readClients() {
    final raw = _box.get('clients', defaultValue: <Map<String, dynamic>>[]) as List;
    return raw
        .map(
          (item) => Map<String, dynamic>.from(item as Map)
            ..putIfAbsent('id', () => 'client-${DateTime.now().microsecondsSinceEpoch}'),
        )
        .toList();
  }

  @override
  void dispose() {
    _name.dispose();
    _contactPerson.dispose();
    _email.dispose();
    _phone.dispose();
    _website.dispose();
    _gstin.dispose();
    _pan.dispose();
    _notes.dispose();
    _placeOfSupply.dispose();
    _billingAddress.dispose();
    _shippingAddress.dispose();
    super.dispose();
  }

  void _loadClient(int index) {
    final client = clients[index];
    _editingIndex = index;
    _name.text = client['name']?.toString() ?? '';
    _contactPerson.text = client['contact_person']?.toString() ?? '';
    _email.text = client['email']?.toString() ?? '';
    _phone.text = client['phone']?.toString() ?? '';
    _website.text = client['website']?.toString() ?? '';
    _gstin.text = client['gstin']?.toString() ?? '';
    _pan.text = client['pan']?.toString() ?? '';
    _notes.text = client['notes']?.toString() ?? '';
    _placeOfSupply.text = client['place_of_supply']?.toString() ?? '';

    _billingAddress.populate(
      client['billing_address'] != null
          ? Map<String, dynamic>.from(client['billing_address'] as Map)
          : null,
    );
    final shipping = client['shipping_address'] != null
        ? Map<String, dynamic>.from(client['shipping_address'] as Map)
        : null;
    _shippingAddress.populate(shipping);
    _shipSameAsBilling = shipping == null || _addressesMatch(shipping);
    if (_shipSameAsBilling) {
      _shippingAddress.populate(null);
    }
    setState(() {});
  }

  void _clearForm() {
    _editingIndex = null;
    _name.clear();
    _contactPerson.clear();
    _email.clear();
    _phone.clear();
    _website.clear();
    _gstin.clear();
    _pan.clear();
    _notes.clear();
    _placeOfSupply.clear();
    _billingAddress.populate(null);
    _shippingAddress.populate(null);
    _shipSameAsBilling = true;
    setState(() {});
  }

  void _saveClient() {
    if (_name.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Client name is required.')),
      );
      return;
    }
    final billing = _billingAddress.value();
    final shipping = _shipSameAsBilling
        ? billing
        : _shippingAddress.value();

    final client = {
      'id': _editingIndex != null
          ? clients[_editingIndex!]['id']
          : 'client-${DateTime.now().microsecondsSinceEpoch}',
      'name': _name.text.trim(),
      'contact_person': _contactPerson.text.trim(),
      'email': _email.text.trim(),
      'phone': _phone.text.trim(),
      'website': _website.text.trim(),
      'gstin': _gstin.text.trim(),
      'pan': _pan.text.trim(),
      'notes': _notes.text.trim(),
      'billing_address': billing,
      'shipping_address': shipping,
      'place_of_supply': _placeOfSupply.text.trim(),
    };

    if (_editingIndex != null) {
      clients[_editingIndex!] = client;
    } else {
      clients.add(client);
    }

    _box.put('clients', clients);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          _editingIndex != null ? 'Client updated.' : 'Client added.',
        ),
      ),
    );
    _clearForm();
  }

  void _removeClient(int index) {
    final removed = clients.removeAt(index);
    _box.put('clients', clients);
    if (_editingIndex == index) {
      _clearForm();
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Removed ${removed['name'] ?? 'client'}')),
    );
  }

  String _displayName(Map<String, dynamic> client) {
    final contact = client['contact_person']?.toString();
    if (contact == null || contact.isEmpty) return client['name']?.toString() ?? '';
    return '${client['name']} — $contact';
  }

  bool _addressesMatch(Map<String, dynamic> other) {
    final billing = _billingAddress.value();
    for (final key in [
      'line1',
      'line2',
      'city',
      'state',
      'state_code',
      'postal_code',
      'country',
      'country_code',
    ]) {
      final a = billing[key]?.toString().trim() ?? '';
      final b = other[key]?.toString().trim() ?? '';
      if (a != b) {
        return false;
      }
    }
    return true;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text(
          'Clients',
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
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  children: [
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          children: [
                            CustTextFields(
                              title: 'COMPANY NAME',
                              textEditingController: _name,
                            ),
                            CustTextFields(
                              title: 'CONTACT PERSON',
                              textEditingController: _contactPerson,
                            ),
                            CustTextFields(
                              title: 'E-MAIL',
                              textEditingController: _email,
                              keyboardType: TextInputType.emailAddress,
                              textCapitalization: TextCapitalization.none,
                            ),
                            CustTextFields(
                              title: 'PHONE',
                              textEditingController: _phone,
                              keyboardType: TextInputType.phone,
                              textCapitalization: TextCapitalization.none,
                            ),
                            CustTextFields(
                              title: 'WEBSITE',
                              textEditingController: _website,
                              textCapitalization: TextCapitalization.none,
                            ),
                            CustTextFields(
                              title: 'GSTIN',
                              textEditingController: _gstin,
                              textCapitalization: TextCapitalization.characters,
                            ),
                            CustTextFields(
                              title: 'PAN',
                              textEditingController: _pan,
                              textCapitalization: TextCapitalization.characters,
                            ),
                            CustTextFields(
                              title: 'NOTES',
                              textEditingController: _notes,
                              maxLines: 3,
                            ),
                            const SizedBox(height: 8),
                            Align(
                              alignment: Alignment.centerLeft,
                              child: Text(
                                'Billing address',
                                style: TextStyle(
                                  color: Colors.grey.shade700,
                                  fontFamily: 'Roboto',
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            CustTextFields(
                              title: 'ADDRESS LINE 1',
                              textEditingController: _billingAddress.line1,
                            ),
                            CustTextFields(
                              title: 'ADDRESS LINE 2',
                              textEditingController: _billingAddress.line2,
                            ),
                            CustTextFields(
                              title: 'CITY',
                              textEditingController: _billingAddress.city,
                            ),
                            CustTextFields(
                              title: 'STATE',
                              textEditingController: _billingAddress.state,
                            ),
                            CustTextFields(
                              title: 'STATE CODE',
                              textEditingController: _billingAddress.stateCode,
                              textCapitalization: TextCapitalization.characters,
                            ),
                            CustTextFields(
                              title: 'POSTAL CODE',
                              textEditingController: _billingAddress.postalCode,
                              keyboardType: TextInputType.number,
                            ),
                            CustTextFields(
                              title: 'COUNTRY',
                              textEditingController: _billingAddress.country,
                            ),
                            CustTextFields(
                              title: 'COUNTRY CODE',
                              textEditingController: _billingAddress.countryCode,
                              textCapitalization: TextCapitalization.characters,
                            ),
                            const SizedBox(height: 12),
                            SwitchListTile(
                              contentPadding: EdgeInsets.zero,
                              title: const Text('Shipping address same as billing?'),
                              value: _shipSameAsBilling,
                              onChanged: (value) {
                                setState(() {
                                  _shipSameAsBilling = value;
                                  if (value) {
                                    _shippingAddress.populate(null);
                                  }
                                });
                              },
                            ),
                            if (!_shipSameAsBilling) ...[
                              CustTextFields(
                                title: 'SHIP ADDRESS LINE 1',
                                textEditingController: _shippingAddress.line1,
                              ),
                              CustTextFields(
                                title: 'SHIP ADDRESS LINE 2',
                                textEditingController: _shippingAddress.line2,
                              ),
                              CustTextFields(
                                title: 'SHIP CITY',
                                textEditingController: _shippingAddress.city,
                              ),
                              CustTextFields(
                                title: 'SHIP STATE',
                                textEditingController: _shippingAddress.state,
                              ),
                              CustTextFields(
                                title: 'SHIP STATE CODE',
                                textEditingController: _shippingAddress.stateCode,
                                textCapitalization: TextCapitalization.characters,
                              ),
                              CustTextFields(
                                title: 'SHIP POSTAL CODE',
                                textEditingController: _shippingAddress.postalCode,
                                keyboardType: TextInputType.number,
                              ),
                              CustTextFields(
                                title: 'SHIP COUNTRY',
                                textEditingController: _shippingAddress.country,
                              ),
                              CustTextFields(
                                title: 'SHIP COUNTRY CODE',
                                textEditingController: _shippingAddress.countryCode,
                                textCapitalization: TextCapitalization.characters,
                              ),
                            ],
                            CustTextFields(
                              title: 'PLACE OF SUPPLY',
                              textEditingController: _placeOfSupply,
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: CustButtons(
                            text: _editingIndex != null ? 'Update client' : 'Save client',
                            onpressed: _saveClient,
                            boxcolor: Colors.blue.shade600,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: CustButtons(
                            text: 'Clear form',
                            onpressed: _clearForm,
                            boxcolor: Colors.grey.shade400,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Saved clients',
                style: TextStyle(
                  color: Colors.grey.shade700,
                  fontFamily: 'Roboto',
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: ListView.separated(
                itemBuilder: (_, index) {
                  final client = clients[index];
                  return Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: ListTile(
                      title: Text(
                        _displayName(client),
                        style: const TextStyle(
                          fontFamily: 'Roboto',
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                        ),
                      ),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if ((client['email']?.toString() ?? '').isNotEmpty)
                            Text(client['email'].toString()),
                          if ((client['phone']?.toString() ?? '').isNotEmpty)
                            Text(client['phone'].toString()),
                          if ((client['place_of_supply']?.toString() ?? '').isNotEmpty)
                            Text('Place of supply: ${client['place_of_supply']}'),
                        ],
                      ),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.edit),
                            onPressed: () => _loadClient(index),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete),
                            onPressed: () => _removeClient(index),
                          ),
                        ],
                      ),
                    ),
                  );
                },
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemCount: clients.length,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
