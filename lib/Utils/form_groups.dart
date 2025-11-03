import 'package:flutter/material.dart';

class AddressControllers {
  AddressControllers({
    String defaultCountry = 'India',
    String defaultCountryCode = 'IN',
  })  : _defaultCountry = defaultCountry,
        _defaultCountryCode = defaultCountryCode,
        line1 = TextEditingController(),
        line2 = TextEditingController(),
        city = TextEditingController(),
        state = TextEditingController(),
        stateCode = TextEditingController(),
        postalCode = TextEditingController(),
        country = TextEditingController(text: defaultCountry),
        countryCode = TextEditingController(text: defaultCountryCode);

  final TextEditingController line1;
  final TextEditingController line2;
  final TextEditingController city;
  final TextEditingController state;
  final TextEditingController stateCode;
  final TextEditingController postalCode;
  final TextEditingController country;
  final TextEditingController countryCode;
  final String _defaultCountry;
  final String _defaultCountryCode;

  void populate(Map<String, dynamic>? value) {
    if (value == null) {
      line1.clear();
      line2.clear();
      city.clear();
      state.clear();
      stateCode.clear();
      postalCode.clear();
      country.text = _defaultCountry;
      countryCode.text = _defaultCountryCode;
      return;
    }
    line1.text = value['line1']?.toString() ?? '';
    line2.text = value['line2']?.toString() ?? '';
    city.text = value['city']?.toString() ?? '';
    state.text = value['state']?.toString() ?? '';
    stateCode.text = value['state_code']?.toString() ?? '';
    postalCode.text = value['postal_code']?.toString() ?? '';
    country.text = value['country']?.toString() ?? country.text;
    countryCode.text = value['country_code']?.toString() ?? countryCode.text;
  }

  Map<String, String> value({
    String? fallbackCountry,
    String? fallbackCountryCode,
  }) {
    return {
      'line1': line1.text.trim(),
      'line2': line2.text.trim(),
      'city': city.text.trim(),
      'state': state.text.trim(),
      'state_code': stateCode.text.trim(),
      'postal_code': postalCode.text.trim(),
      'country': country.text.trim().isEmpty
          ? (fallbackCountry ?? _defaultCountry)
          : country.text.trim(),
      'country_code': countryCode.text.trim().isEmpty
          ? (fallbackCountryCode ?? _defaultCountryCode)
          : countryCode.text.trim(),
    };
  }

  void dispose() {
    line1.dispose();
    line2.dispose();
    city.dispose();
    state.dispose();
    stateCode.dispose();
    postalCode.dispose();
    country.dispose();
    countryCode.dispose();
  }
}

class BankControllers {
  BankControllers()
      : bankName = TextEditingController(),
        branch = TextEditingController(),
        accountName = TextEditingController(),
        accountNo = TextEditingController(),
        ifsc = TextEditingController(),
        swift = TextEditingController(),
        iban = TextEditingController(),
        upiId = TextEditingController();

  final TextEditingController bankName;
  final TextEditingController branch;
  final TextEditingController accountName;
  final TextEditingController accountNo;
  final TextEditingController ifsc;
  final TextEditingController swift;
  final TextEditingController iban;
  final TextEditingController upiId;

  void populate(Map<String, dynamic>? value) {
    if (value == null) return;
    bankName.text = value['bank_name']?.toString() ?? '';
    branch.text = value['branch']?.toString() ?? '';
    accountName.text = value['account_name']?.toString() ?? '';
    accountNo.text = value['account_no']?.toString() ?? '';
    ifsc.text = value['ifsc']?.toString() ?? '';
    swift.text = value['swift']?.toString() ?? '';
    iban.text = value['iban']?.toString() ?? '';
    upiId.text = value['upi_id']?.toString() ?? '';
  }

  Map<String, String> value() {
    return {
      'bank_name': bankName.text.trim(),
      'branch': branch.text.trim(),
      'account_name': accountName.text.trim(),
      'account_no': accountNo.text.trim(),
      'ifsc': ifsc.text.trim(),
      'swift': swift.text.trim(),
      'iban': iban.text.trim(),
      'upi_id': upiId.text.trim(),
    };
  }

  void dispose() {
    bankName.dispose();
    branch.dispose();
    accountName.dispose();
    accountNo.dispose();
    ifsc.dispose();
    swift.dispose();
    iban.dispose();
    upiId.dispose();
  }
}

class BrandingControllers {
  BrandingControllers()
      : logoUrl = TextEditingController(),
        accentColor = TextEditingController(text: '#0057FF'),
        footerText = TextEditingController();

  final TextEditingController logoUrl;
  final TextEditingController accentColor;
  final TextEditingController footerText;

  void populate(Map<String, dynamic>? value) {
    if (value == null) return;
    logoUrl.text = value['logo_url']?.toString() ?? '';
    accentColor.text = value['accent_color']?.toString() ?? accentColor.text;
    footerText.text = value['footer_text']?.toString() ?? '';
  }

  Map<String, String> value() {
    return {
      'logo_url': logoUrl.text.trim(),
      'accent_color': accentColor.text.trim().isEmpty
          ? '#0057FF'
          : accentColor.text.trim(),
      'footer_text': footerText.text.trim(),
    };
  }

  void dispose() {
    logoUrl.dispose();
    accentColor.dispose();
    footerText.dispose();
  }
}
