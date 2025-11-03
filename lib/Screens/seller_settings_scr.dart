import 'package:flutter/material.dart';
import 'package:hive/hive.dart';

import '../Utils/form_groups.dart';
import '../Utils/reusables.dart';

class SellerSettings extends StatefulWidget {
  const SellerSettings({super.key});

  @override
  State<SellerSettings> createState() => _SellerSettingsState();
}

class _SellerSettingsState extends State<SellerSettings> {
  final _box = Hive.box('settings');

  final _name = TextEditingController();
  final _contactPerson = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _website = TextEditingController();
  final _gstin = TextEditingController();
  final _pan = TextEditingController();
  final _notes = TextEditingController();
  final _cin = TextEditingController();
  final _placeOfSupply = TextEditingController();

  final AddressControllers _billingAddress = AddressControllers();
  final BankControllers _bank = BankControllers();
  final BrandingControllers _branding = BrandingControllers();

  bool _reverseCharge = false;
  bool _eInvoice = false;

  @override
  void initState() {
    super.initState();
    _loadFromBox();
  }

  void _loadFromBox() {
    final data = Map<String, dynamic>.from(
      _box.get('seller', defaultValue: <String, dynamic>{}) as Map,
    );
    _name.text = data['name']?.toString() ?? '';
    _contactPerson.text = data['contact_person']?.toString() ?? '';
    _email.text = data['email']?.toString() ?? '';
    _phone.text = data['phone']?.toString() ?? '';
    _website.text = data['website']?.toString() ?? '';
    _gstin.text = data['gstin']?.toString() ?? '';
    _pan.text = data['pan']?.toString() ?? '';
    _notes.text = data['notes']?.toString() ?? '';
    _cin.text = data['cin']?.toString() ?? '';
    _placeOfSupply.text =
        data['tax_prefs']?['place_of_supply']?.toString() ?? '';
    _reverseCharge =
        (data['tax_prefs']?['reverse_charge'] as bool?) ?? _reverseCharge;
    _eInvoice = (data['tax_prefs']?['e_invoice'] as bool?) ?? _eInvoice;

    _billingAddress.populate(
      data['billing_address'] != null
          ? Map<String, dynamic>.from(data['billing_address'] as Map)
          : null,
    );
    _bank.populate(
      data['bank'] != null
          ? Map<String, dynamic>.from(data['bank'] as Map)
          : null,
    );
    _branding.populate(
      data['branding'] != null
          ? Map<String, dynamic>.from(data['branding'] as Map)
          : null,
    );
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
    _cin.dispose();
    _placeOfSupply.dispose();
    _billingAddress.dispose();
    _bank.dispose();
    _branding.dispose();
    super.dispose();
  }

  void _save() {
    final seller = {
      'name': _name.text.trim(),
      'contact_person': _contactPerson.text.trim(),
      'email': _email.text.trim(),
      'phone': _phone.text.trim(),
      'website': _website.text.trim(),
      'gstin': _gstin.text.trim(),
      'pan': _pan.text.trim(),
      'notes': _notes.text.trim(),
      'cin': _cin.text.trim(),
      'billing_address': _billingAddress.value(),
      'bank': _bank.value(),
      'tax_prefs': {
        'place_of_supply': _placeOfSupply.text.trim(),
        'reverse_charge': _reverseCharge,
        'e_invoice': _eInvoice,
      },
      'branding': _branding.value(),
    };

    _box.put('seller', seller);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Seller profile saved.')),
    );
  }

  Widget _section(String title, List<Widget> children) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
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
              title,
              style: const TextStyle(
                fontFamily: 'Roboto',
                fontSize: 14,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 12),
            ...children,
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text(
          'Company Defaults',
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
        child: SingleChildScrollView(
          child: Column(
            children: [
              _section('Business identity', [
                CustTextFields(title: 'COMPANY NAME', textEditingController: _name),
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
              ]),
              _section('Compliance', [
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
                  title: 'CIN',
                  textEditingController: _cin,
                  textCapitalization: TextCapitalization.characters,
                ),
                CustTextFields(
                  title: 'INTERNAL NOTES',
                  textEditingController: _notes,
                  maxLines: 3,
                ),
              ]),
              _section('Billing address', [
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
              ]),
              _section('Banking details', [
                CustTextFields(
                  title: 'BANK NAME',
                  textEditingController: _bank.bankName,
                ),
                CustTextFields(
                  title: 'BRANCH',
                  textEditingController: _bank.branch,
                ),
                CustTextFields(
                  title: 'ACCOUNT NAME',
                  textEditingController: _bank.accountName,
                ),
                CustTextFields(
                  title: 'ACCOUNT NUMBER',
                  textEditingController: _bank.accountNo,
                  keyboardType: TextInputType.number,
                ),
                CustTextFields(
                  title: 'IFSC',
                  textEditingController: _bank.ifsc,
                  textCapitalization: TextCapitalization.characters,
                ),
                CustTextFields(
                  title: 'SWIFT',
                  textEditingController: _bank.swift,
                  textCapitalization: TextCapitalization.characters,
                ),
                CustTextFields(
                  title: 'IBAN',
                  textEditingController: _bank.iban,
                  textCapitalization: TextCapitalization.characters,
                ),
                CustTextFields(
                  title: 'UPI ID',
                  textEditingController: _bank.upiId,
                  textCapitalization: TextCapitalization.none,
                ),
              ]),
              _section('Tax preferences', [
                CustTextFields(
                  title: 'PLACE OF SUPPLY',
                  textEditingController: _placeOfSupply,
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Reverse charge applicable?'),
                  value: _reverseCharge,
                  onChanged: (value) => setState(() => _reverseCharge = value),
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('E-invoice enabled?'),
                  value: _eInvoice,
                  onChanged: (value) => setState(() => _eInvoice = value),
                ),
              ]),
              _section('Branding', [
                CustTextFields(
                  title: 'LOGO URL',
                  textEditingController: _branding.logoUrl,
                  textCapitalization: TextCapitalization.none,
                ),
                CustTextFields(
                  title: 'ACCENT COLOR (HEX)',
                  textEditingController: _branding.accentColor,
                  textCapitalization: TextCapitalization.characters,
                ),
                CustTextFields(
                  title: 'FOOTER TEXT',
                  textEditingController: _branding.footerText,
                  maxLines: 2,
                ),
              ]),
              const SizedBox(height: 12),
              CustButtons(
                text: 'Save',
                onpressed: _save,
                boxcolor: Colors.blue.shade600,
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}
