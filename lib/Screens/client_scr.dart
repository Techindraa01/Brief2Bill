import 'package:flutter/material.dart';
import 'package:hive/hive.dart';

import '../Utils/reusables.dart';

class ClientsScreen extends StatefulWidget {
  const ClientsScreen({super.key});

  @override
  State<ClientsScreen> createState() => _ClientsScreenState();
}

class _ClientsScreenState extends State<ClientsScreen> {
  final _box = Hive.box('settings');
  final _name = TextEditingController();
  final _email = TextEditingController();
  List clients = [];

  @override
  void initState() {
    super.initState();
    clients = _box.get('clients', defaultValue: []) as List;
  }

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    super.dispose();
  }

  void _add() {
    final c = {'name': _name.text, 'email': _email.text};
    clients.add(c);
    _box.put('clients', clients);
    setState(() {});
    _name.clear();
    _email.clear();
  }
  String toTitleCase(String text) {
    if (text.isEmpty) return text;
    return text
        .split(' ')
        .map((word) =>
    word.isEmpty ? '' : '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}')
        .join(' ');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(title: const Text('Clients', style: TextStyle(color: Colors.white, fontFamily: 'Roboto', fontSize: 16, fontWeight: FontWeight.w600)
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
      ),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Container(
              decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10)
              ),
              child: Padding(
                  padding: const EdgeInsets.all(8.0),
                child: Column(
                  children: [
                    CustTextFields( title: 'NAME', textEditingController: _name,),
                    Divider(color: Colors.grey.shade300,thickness: 1,),
                    CustTextFields( title: 'E-MAIL', textEditingController: _email,),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),
            CustButtons(text: "Add", onpressed: _add, boxcolor: Colors.blue.shade600,),
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Expanded(child: Divider(color: Colors.grey.shade400, thickness: 1)),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8.0),
                  child: Text("Clients"),
                ),
                Expanded(child: Divider(color: Colors.grey.shade400, thickness: 1)),
              ],
            ),
            SizedBox(height: 15,),
            Expanded(
              child: ListView.builder(
                itemCount: clients.length,
                itemBuilder: (_, i) {
                  final c = clients[i];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Container(
                      decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(10)
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(8.0),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text( toTitleCase(c['name'] ?? ''), style: TextStyle(color: Colors.black, fontFamily: 'Roboto', fontWeight: FontWeight.w600, fontSize: 14),),
                                Text(c['email'] ?? '', style: TextStyle(color: Colors.grey, fontFamily: 'Roboto', fontWeight: FontWeight.w600, fontSize: 12),),
                              ],
                            ),
                                          IconButton(
                          icon: const Icon(Icons.delete),
                          onPressed: () {},
                        ),
                          ],
                        ),
                      ),
                    ),
                  );


                  //   ListTile(
                  //
                  //   title: Text(c['name'] ?? ''),
                  //   subtitle: Text(c['email'] ?? ''),
                  //   trailing: IconButton(
                  //     icon: const Icon(Icons.edit),
                  //     onPressed: () {},
                  //   ),
                  // );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
