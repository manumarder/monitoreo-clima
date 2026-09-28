import unittest

from monitor_clima import extract_weather_report, find_matches


class FindMatchesTests(unittest.TestCase):
    def test_matches_case_and_accents_without_repeating_substrings(self) -> None:
        content = "Hay alerta por TORMENTA en Corrientes con lluvias."

        matches = find_matches(content, ("alerta", "tormenta", "lluvia"))

        self.assertEqual(matches, ["alerta", "tormenta"])

    def test_matches_phrase_with_accents_and_variable_spacing(self) -> None:
        matches = find_matches(
            "Pronostico: lluvia   intensa para la ciudad.",
            ("lluvia intensa", "granizo"),
        )

        self.assertEqual(matches, ["lluvia intensa"])

    def test_empty_keywords_and_partial_words_do_not_match(self) -> None:
        matches = find_matches("Se esperan tormentas aisladas.", ("", "tormenta"))

        self.assertEqual(matches, [])


class ExtractWeatherReportTests(unittest.TestCase):
    def test_extracts_city_summary_and_detail_without_alert_map_news(self) -> None:
        content = """
        Tiempo en Corrientes
        10:36 | Lunes
        Soleado 32 grados Sensacion de 37 grados
        Por horas Calor Humedo Sofocante en las proximas horas
        Ultima hora
        El Servicio Meteorologico Nacional emitio alerta naranja en Buenos Aires
        Clima en Corrientes hoy, 28 de septiembre
        Hoy en Corrientes, nubes y claros esta manana, con temperaturas alrededor de 29 grados.
        Por la tarde, tendremos nubes y claros y durante la noche parcialmente nuboso.
        11:00 32° Soleado Sensacion termica 37 grados Noreste 7 - 19 km/h
        12:00 30% 0.7 mm 34° Lluvia debil Sensacion termica 40 grados Norte 5 - 20 km/h
        Tiempo: PDF
        Clima en Resistencia hoy, 28 de septiembre
        Hoy en Resistencia, tormentas durante la tarde.
        """

        report = extract_weather_report(content, "Corrientes")

        self.assertIsNotNone(report)
        assert report is not None
        self.assertIn("Ahora: Soleado 32 grados Sensacion de 37 grados", report)
        self.assertIn("Hoy (28 de septiembre): nubes y claros esta manana", report)
        self.assertIn("11:00 | 32° | Soleado", report)
        self.assertIn("12:00 | 34° | Lluvia debil | 30% 0.7 mm", report)
        self.assertNotIn("Sensacion termica", report)
        self.assertNotIn("Noreste", report)
        self.assertNotIn("FPS", report)
        self.assertNotIn("Clima en Corrientes hoy", report)
        self.assertNotIn("Hoy en Corrientes", report)
        self.assertNotIn("Buenos Aires", report)
        self.assertNotIn("Resistencia", report)
        self.assertNotIn("10:36", report)

    def test_returns_none_when_city_forecast_is_missing(self) -> None:
        report = extract_weather_report(
            "Tiempo en Buenos Aires. Clima en Buenos Aires hoy, lluvia debil.",
            "Corrientes",
        )

        self.assertIsNone(report)


if __name__ == "__main__":
    unittest.main()