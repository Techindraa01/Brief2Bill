import "package:flutter/material.dart";

import "home_draft.dart";

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}
class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _init().then((_) => Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const HomeDraft())));
  }
  Future<void> _init() async {
// Initialize caches, SDK placeholders
    await Future.delayed(const Duration(milliseconds: 350));
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(body: Center(child: Text('DocForge', style: Theme.of(context).textTheme.headlineMedium)));
  }
}