import 'package:flutter/material.dart';

class CustTextFields extends StatefulWidget {
  final String title;
  final TextEditingController textEditingController;
  final TextInputType keyboardType;
  final int maxLines;
  final String? hintText;
  final TextCapitalization textCapitalization;


  const CustTextFields({
    super.key,
    required this.title,
    required this.textEditingController,
    this.keyboardType = TextInputType.text,
    this.maxLines = 1,
    this.hintText,
    this.textCapitalization = TextCapitalization.sentences,
  });

  @override
  State<CustTextFields> createState() => _CustTextFieldsState();
}

class _CustTextFieldsState extends State<CustTextFields> {
  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(height: MediaQuery.heightOf(context) * 0.01),
        Text(widget.title, style: TextStyle(color: Colors.grey.shade900, fontFamily: 'Roboto', fontSize: 12, fontWeight: FontWeight.w600)),
        SizedBox(height: MediaQuery.heightOf(context) * 0.01),
        TextField(
          controller: widget.textEditingController,
          maxLines: widget.maxLines,
          keyboardType: widget.keyboardType,
          textCapitalization: widget.textCapitalization,
          onChanged: (_) => setState(() {}),
          decoration:  InputDecoration(
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
                borderSide:  BorderSide(color: Colors.grey.shade600, width: 2),
              ),
              hintText: widget.hintText,
          ),
        ),
        SizedBox(height: MediaQuery.heightOf(context) * 0.01),
      ],
    );
  }
}


class CustButtons extends StatelessWidget {
  final String text;
  final VoidCallback onpressed;
  final Color boxcolor;
  const CustButtons({super.key, required this.text, required this.onpressed, required this.boxcolor});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onpressed,
      child: Container(
          width: double.infinity,
          height: MediaQuery.heightOf(context)* 0.06,
          decoration: BoxDecoration(
              color: boxcolor,
              borderRadius: BorderRadius.circular(10)),
          child :
              Center(child: Text(text,style: TextStyle(color: Colors.white, fontFamily: 'Roboto', fontSize: 14, fontWeight: FontWeight.w600),)),

      ),
    );
  }
}
