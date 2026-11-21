import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:material_ui/material_ui.dart';

const apiUrl = 'https://sudan-food-price-api.onrender.com/predict';

const orange = Color(0xFFC2410C);
const peach = Color(0xFFFFEDD5);
const cardBorder = Color(0xFFFED7AA);
const fieldBorder = Color(0xFFFDBA74);
const textBrown = Color(0xFF431407);
const labelBrown = Color(0xFF7C2D12);
const background = Color(0xFFFFF7ED);
const errorRed = Color(0xFF7F1D1D);

void main() => runApp(const SouqCastApp());

class SouqCastApp extends StatelessWidget {
  const SouqCastApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SouqCast',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: orange,
        scaffoldBackgroundColor: background,
      ),
      home: const PredictPage(),
    );
  }
}

class PredictPage extends StatefulWidget {
  const PredictPage({super.key});

  @override
  State<PredictPage> createState() => _PredictPageState();
}

class _PredictPageState extends State<PredictPage> {
  final market = TextEditingController();
  final admin1 = TextEditingController();
  final latitude = TextEditingController();
  final longitude = TextEditingController();
  final category = TextEditingController();
  final commodity = TextEditingController();
  final pricetype = TextEditingController();
  final year = TextEditingController();
  final month = TextEditingController();

  bool loading = false;
  String? price;
  String? details;
  String? error;

  // API field names -> labels shown in the app
  static const labels = {
    'market': 'Market',
    'admin1': 'State (admin1)',
    'latitude': 'Latitude',
    'longitude': 'Longitude',
    'category': 'Category',
    'commodity': 'Commodity',
    'pricetype': 'Price type',
    'year': 'Year',
    'month': 'Month',
  };

  @override
  void dispose() {
    for (final c in [market, admin1, latitude, longitude, category, commodity, pricetype, year, month]) {
      c.dispose();
    }
    super.dispose();
  }

  void showError(String message) {
    setState(() {
      error = message;
      price = null;
    });
  }

  Future<void> predict() async {
    FocusScope.of(context).unfocus();

    // missing values are caught here, before calling the API
    final fields = {
      'market': market,
      'admin1': admin1,
      'latitude': latitude,
      'longitude': longitude,
      'category': category,
      'commodity': commodity,
      'pricetype': pricetype,
      'year': year,
      'month': month,
    };
    for (final entry in fields.entries) {
      if (entry.value.text.trim().isEmpty) {
        showError('${labels[entry.key]} is missing.');
        return;
      }
    }

    // wrong types are caught here too
    final lat = double.tryParse(latitude.text.trim());
    final lon = double.tryParse(longitude.text.trim());
    final y = int.tryParse(year.text.trim());
    final m = int.tryParse(month.text.trim());
    if (lat == null) return showError('Latitude must be a number, e.g. 11.79.');
    if (lon == null) return showError('Longitude must be a number, e.g. 34.36.');
    if (y == null) return showError('Year must be a whole number, e.g. 2024.');
    if (m == null) return showError('Month must be a whole number from 1 to 12.');

    setState(() {
      loading = true;
      error = null;
      price = null;
    });

    try {
      final response = await http
          .post(
            Uri.parse(apiUrl),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'market': market.text.trim(),
              'admin1': admin1.text.trim(),
              'category': category.text.trim(),
              'commodity': commodity.text.trim(),
              'pricetype': pricetype.text.trim(),
              'latitude': lat,
              'longitude': lon,
              'year': y,
              'month': m,
            }),
          )
          .timeout(const Duration(seconds: 90)); // Render's free plan can take a minute to wake up
      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        setState(() {
          price = (data['predicted_price_usd_per_kg'] as num).toStringAsFixed(2);
          details = '${commodity.text.trim()} · ${market.text.trim()} · $m/$y';
        });
      } else {
        showError(readableError(data));
      }
    } on TimeoutException {
      showError('The server took too long to answer. Please try again.');
    } catch (_) {
      showError('Could not reach the server. Check your internet and try again.');
    } finally {
      setState(() => loading = false);
    }
  }

  // FastAPI sends validation errors as a list under "detail"
  String readableError(dynamic data) {
    final detail = data['detail'];
    if (detail is List && detail.isNotEmpty) {
      final first = detail.first;
      final field = (first['loc'] as List).last.toString();
      return '${labels[field] ?? field}: ${first['msg']}';
    }
    return detail?.toString() ?? 'Something went wrong. Please try again.';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: orange,
        foregroundColor: Colors.white,
        toolbarHeight: 72,
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('SouqCast', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            Text(
              'Wartime food price predictions for Sudanese markets',
              style: TextStyle(fontSize: 12.5, color: peach),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _section('MARKET', Icons.storefront_outlined, [
              _field('Market', market, hint: 'e.g. Damazin'),
              _field('State (admin1)', admin1, hint: 'e.g. Blue Nile'),
            ]),
            _section('LOCATION', Icons.place_outlined, [
              _pair(
                _field('Latitude', latitude, hint: 'e.g. 11.79', decimal: true),
                _field('Longitude', longitude, hint: 'e.g. 34.36', decimal: true),
              ),
            ]),
            _section('FOOD', Icons.shopping_basket_outlined, [
              _field('Category', category, hint: 'e.g. cereals and tubers'),
              _field('Commodity', commodity, hint: 'e.g. Sorghum'),
            ]),
            _section('PRICE TYPE', Icons.sell_outlined, [
              _field('Price type', pricetype, hint: 'Retail'),
            ]),
            _section('DATE', Icons.calendar_month_outlined, [
              _pair(
                _field('Year', year, hint: 'e.g. 2024', number: true),
                _field('Month', month, hint: '1 to 12', number: true),
              ),
            ]),
            const SizedBox(height: 4),
            SizedBox(
              height: 52,
              child: FilledButton(
                onPressed: loading ? null : predict,
                style: FilledButton.styleFrom(
                  backgroundColor: orange,
                  disabledBackgroundColor: orange.withValues(alpha: 0.6),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: loading
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white),
                      )
                    : const Text('Predict', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 12),
            _resultArea(),
          ],
        ),
      ),
    );
  }

  Widget _section(String title, IconData icon, List<Widget> children) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: cardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: orange),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 0.8, color: orange),
              ),
            ],
          ),
          const SizedBox(height: 10),
          for (final child in children) ...[child, const SizedBox(height: 10)],
        ],
      ),
    );
  }

  Widget _pair(Widget left, Widget right) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(child: left),
        const SizedBox(width: 10),
        Expanded(child: right),
      ],
    );
  }

  Widget _field(String label, TextEditingController controller,
      {String? hint, bool number = false, bool decimal = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: labelBrown)),
        const SizedBox(height: 5),
        TextField(
          controller: controller,
          keyboardType: decimal
              ? const TextInputType.numberWithOptions(decimal: true)
              : number
                  ? TextInputType.number
                  : TextInputType.text,
          style: const TextStyle(fontSize: 15, color: textBrown),
          decoration: InputDecoration(
            hintText: hint,
            isDense: true,
            filled: true,
            fillColor: Colors.white,
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 13),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: fieldBorder, width: 1.5),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: orange, width: 2),
            ),
          ),
        ),
      ],
    );
  }

  // one display area for the waiting message, the price or an error
  Widget _resultArea() {
    final isError = error != null;
    final isPrice = price != null;

    IconData icon = Icons.info_outline;
    String title = 'Result';
    String body = 'Fill in all fields and press Predict.';
    if (loading) {
      icon = Icons.hourglass_top;
      body = 'Predicting… the server may take up to a minute to wake up.';
    } else if (isError) {
      icon = Icons.error_outline;
      title = 'Please check your input';
      body = error!;
    } else if (isPrice) {
      icon = Icons.check_circle_outline;
      title = 'Predicted price';
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isError ? const Color(0xFFFEF2F2) : peach,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: isError ? const Color(0xFFFCA5A5) : fieldBorder, width: 1.5),
      ),
      child: Row(
        children: [
          Icon(icon, size: 28, color: isError ? errorRed : orange),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: isError ? errorRed : labelBrown),
                ),
                const SizedBox(height: 2),
                if (isPrice && !loading) ...[
                  Text('\$$price per kg',
                      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: textBrown)),
                  Text(details!, style: const TextStyle(fontSize: 12, color: labelBrown)),
                ] else
                  Text(body, style: TextStyle(fontSize: 15, color: isError ? errorRed : textBrown)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
