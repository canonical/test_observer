import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:testcase_dashboard/board_view.dart';

void main() {
  runApp(const ProviderScope(child: DashboardApp()));
}

class DashboardApp extends StatelessWidget {
  const DashboardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
        home: Scaffold(
            appBar: AppBar(
              title: const Text(
                "Snap Update Verification",
                style: TextStyle(
                  color: Color(0xff5E2750),
                  fontFamily: "Ubuntu",
                  fontWeight: FontWeight.bold,
                  fontSize: 36,
                ),
              ),
              backgroundColor: Colors.white,
              elevation: 0,
              leading: Builder(
                builder: (BuildContext context) {
                  return IconButton(
                    icon: const Icon(
                      Icons.menu,
                      color: Colors.black,
                    ),
                    onPressed: () {
                      Scaffold.of(context).openDrawer();
                    },
                    tooltip:
                        MaterialLocalizations.of(context).openAppDrawerTooltip,
                  );
                },
              ),
            ),
            drawerScrimColor: Colors.transparent,
            drawer: Drawer(
              backgroundColor: const Color(0xff5E2750),
              child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.start,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Logo(),
                      Text(
                        "Kernel Testing",
                        style: TextStyle(
                          color: Colors.white,
                          fontFamily: "Ubuntu",
                          fontWeight: FontWeight.normal,
                          fontSize: 24,
                        ),
                      ),
                      SizedBox(height: 10),
                      Text(
                        "Snap Testing",
                        style: TextStyle(
                          color: Colors.white,
                          fontFamily: "Ubuntu",
                          fontWeight: FontWeight.normal,
                          fontSize: 24,
                        ),
                      ),
                      SizedBox(height: 10),
                      Text(
                        "Image Testing",
                        style: TextStyle(
                          color: Colors.white,
                          fontFamily: "Ubuntu",
                          fontWeight: FontWeight.normal,
                          fontSize: 24,
                        ),
                      ),
                    ],
                  )),
            ),
            body: const Padding(
              padding: EdgeInsets.only(top: 20, left: 50),
              child: BoardView(),
            )));
  }
}

class SideLayout extends StatelessWidget {
  const SideLayout({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
        color: const Color(0xff772953),
        child: Column(
          children: <Widget>[
            SizedBox(
                child: Image.asset('../external/media/canonical_white_hex.png'))
          ],
        ),
      ),
    );
  }
}

class Logo extends StatelessWidget {
  const Logo({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SizedBox(
        height: 100,
        child: DrawerHeader(
            decoration: const BoxDecoration(
              color: Colors.transparent,
            ),
            child: Row(
              children: [
                SizedBox(
                    width: 50,
                    height: 50,
                    child: Image.asset("../external/media/ubuntu.png")),
                const SizedBox(width: 10),
                const Text("Ubuntu\nCertification",
                    style: TextStyle(
                      color: Colors.white,
                      fontFamily: "Ubuntu",
                      fontWeight: FontWeight.bold,
                      fontSize: 20,
                    )),
              ],
            )));
  }
}
