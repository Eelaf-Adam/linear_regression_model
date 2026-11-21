import 'package:flutter_test/flutter_test.dart';

import 'package:souqcast/main.dart';

void main() {
  testWidgets('shows the Predict button', (tester) async {
    await tester.pumpWidget(const SouqCastApp());
    expect(find.text('Predict'), findsOneWidget);
  });
}
