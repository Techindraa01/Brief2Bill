import 'package:flutter/material.dart';
import 'package:hive/hive.dart';

class ClientsScreen extends StatefulWidget { const ClientsScreen({super.key}); @override State<ClientsScreen> createState() => _ClientsScreenState(); }
class _ClientsScreenState extends State<ClientsScreen>{
  final _box = Hive.box('settings');
  final _name = TextEditingController();
  final _email = TextEditingController();
  List clients = [];
  @override void initState(){ super.initState(); clients = _box.get('clients', defaultValue: []) as List; }
  @override void dispose(){ _name.dispose(); _email.dispose(); super.dispose(); }
  void _add(){ final c={'name':_name.text,'email':_email.text}; clients.add(c); _box.put('clients', clients); setState((){}); _name.clear(); _email.clear(); }
  @override Widget build(BuildContext context){ return Scaffold(appBar: AppBar(title: const Text('Clients')), body: Padding(padding: const EdgeInsets.all(12), child: Column(children: [TextField(controller: _name, decoration: const InputDecoration(labelText:'Name')), TextField(controller: _email, decoration: const InputDecoration(labelText:'Email')), ElevatedButton(onPressed: _add, child: const Text('Add')), Expanded(child: ListView.builder(itemCount: clients.length,itemBuilder: (_,i){ final c=clients[i]; return ListTile(title: Text(c['name'] ?? ''), subtitle: Text(c['email'] ?? ''), trailing: IconButton(icon: const Icon(Icons.edit), onPressed: (){})); })) ]))); }
}
