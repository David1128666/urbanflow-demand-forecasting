import unittest

from app.locales import en, zh_CN


class LocaleCompletenessTest(unittest.TestCase):
    def test_english_and_chinese_have_the_same_keys(self) -> None:
        self.assertEqual(
            set(en.MESSAGES),
            set(zh_CN.MESSAGES),
        )


if __name__ == "__main__":
    unittest.main()
