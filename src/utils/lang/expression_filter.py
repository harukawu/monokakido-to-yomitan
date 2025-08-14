from typing import List, Tuple, Optional
from sudachipy import tokenizer
from sudachipy import dictionary
import jamdict
import jaconv

from utils.lang import KanjiUtils


class ExpressionFilter:
    _tokenizer_obj = None

    @classmethod
    def _get_tokenizer(cls):
        if cls._tokenizer_obj is None:
            cls._tokenizer_obj = dictionary.Dictionary(dict="full").create()
        return cls._tokenizer_obj

    @staticmethod
    def filter_full_forms(kanji_forms: List[str], reading_forms: List[str]) -> List[Tuple[str, str]]:
        """
        Filter to keep meaningful variations of full-form expressions with correct readings.
        """
        if not kanji_forms:
            return [('', kana) for kana in reading_forms]

        if not reading_forms:
            return [(kanji, '') for kanji in kanji_forms]

        # Find the best complete kanji forms (may return multiple)
        best_expression_forms = ExpressionFilter._find_best_complete_form(kanji_forms)
        if not best_expression_forms:
            return []

        # Find valid kanji-reading pairs
        valid_pairs = []
        for kanji_form in best_expression_forms:
            matching_readings = ExpressionFilter._find_best_reading_match(kanji_form, reading_forms)
            for reading in matching_readings:
                valid_pairs.append((kanji_form, reading))

        # Remove duplicates while preserving order
        seen = set()
        unique_pairs = []
        for pair in valid_pairs:
            if pair not in seen:
                seen.add(pair)
                unique_pairs.append(pair)

        return unique_pairs

    @staticmethod
    def _find_best_complete_form(kanji_forms: List[str]) -> Optional[str]:
        """
        Find the single best complete kanji form from the candidates.
        Uses Sudachi for morphological analysis to better understand compound structures.
        """
        if not kanji_forms:
            return None

        tokenizer_obj = ExpressionFilter._get_tokenizer()
        filtered_forms = []

        # Step 1: Remove substrings of other forms
        filtered_forms = ExpressionFilter.filter_substrings(kanji_forms)

        # Step 2: Analyze forms and find the max score
        scored_forms = []
        max_kanji_tokens = 0

        for form in filtered_forms:
            tokens = tokenizer_obj.tokenize(form, tokenizer.Tokenizer.SplitMode.C)

            # Count tokens that contain at least one kanji character
            kanji_count = sum(1 for char in form if KanjiUtils.is_kanji(char))

            scored_forms.append((kanji_count, form))
            if kanji_count > max_kanji_tokens:
                max_kanji_tokens = kanji_count

        # Step 3: Filter only those with the highest kanji token count
        best_forms = [form for score, form in scored_forms if score == max_kanji_tokens]

        return best_forms if best_forms else None

    @staticmethod
    def filter_substrings(forms: List[str]) -> List[str]:
        filtered_readings = []
        for form in forms:
            if not any(form != other and form in other for other in forms):
                filtered_readings.append(form)

        return filtered_readings

    @staticmethod
    def _find_best_reading_match(kanji_form: str, reading_forms: List[str]) -> Optional[List[str]]:
        """
        Find the reading(s) that best matches the given kanji form.
        """
        if not reading_forms:
            return None

        filtered_readings = ExpressionFilter.filter_substrings(reading_forms)
        if len(filtered_readings) == 1:
            return filtered_readings

        tokenizer_obj = ExpressionFilter._get_tokenizer()
        kanji_tokens = tokenizer_obj.tokenize(kanji_form, tokenizer.Tokenizer.SplitMode.C)
        tokenized_reading = ''.join(token.reading_form() for token in kanji_tokens)

        scored_readings = []
        for reading_form in filtered_readings:
            score = 0.0

            # Skip if the kanji form has kana that is not present in the reading
            kana_in_kanji_form = set([c for c in kanji_form if KanjiUtils.is_hiragana(c) or KanjiUtils.is_katakana(c)])
            if any(c for c in kana_in_kanji_form if c not in reading_form and c != 'ケ'):
                continue

            # Perfect match with tokenized reading gets highest score
            if tokenized_reading == reading_form:
                score += len(reading_form) * 5

            # Enhanced kanji-reading alignment scoring
            kanji_reading_score = ExpressionFilter._score_kanji_reading_alignment(
                kanji_form, reading_form
            )
            score += kanji_reading_score

            # Bonus for suffix matching
            if KanjiUtils.is_hiragana(kanji_form[-1]) or KanjiUtils.is_katakana(kanji_form[-1]):
                suffix_score = KanjiUtils.longest_common_suffix(reading_form, kanji_form)
                score += suffix_score * 10

            # Bonus for prefix matching
            if KanjiUtils.is_hiragana(kanji_form[0]) or KanjiUtils.is_katakana(kanji_form[0]):
                prefix_score = KanjiUtils.longest_common_prefix(reading_form, kanji_form)
                score += prefix_score * 10

            # Additional scoring for partial kana matches
            kana_overlap = sum(1 for c in kana_in_kanji_form if c in reading_form)
            score += kana_overlap * 5

            scored_readings.append((score, reading_form))

        if not scored_readings:
            return []

        max_score = max(score for score, _ in scored_readings)

        if max_score >= 100: threshold = max_score * 0.75
        elif max_score >= 50: threshold = max_score * 0.7
        elif max_score >= 25: threshold = max_score * 0.7
        elif max_score >= 10: threshold = max_score * 0.8
        else:  # Lower confidence matches
            threshold = max_score * 0.9

        best_readings = [
            reading for score, reading in scored_readings
            if score >= threshold
        ]

        return best_readings

    @staticmethod
    def _score_kanji_reading_alignment(kanji_form: str, reading_form: str) -> float:
        """
        Score how well the reading aligns with the kanji characters.
        focusing on coverage and relevance.
        """
        tokenizer_obj = ExpressionFilter._get_tokenizer()
        kanji_tokens = tokenizer_obj.tokenize(kanji_form, tokenizer.Tokenizer.SplitMode.B)

        if not kanji_tokens:
            return 0.0

        alignment_score = 0.0
        reading_coverage = set()  # Track which parts of reading we've matched

        for token in kanji_tokens:
            surface = token.surface()

            # Handle kana parts directly
            if all(KanjiUtils.is_hiragana(c) or KanjiUtils.is_katakana(c) for c in surface):
                if surface in reading_form:
                    alignment_score += len(surface) * 3  # Good match for kana
                    # Mark positions as covered
                    start_pos = reading_form.find(surface)
                    if start_pos != -1:
                        reading_coverage.update(range(start_pos, start_pos + len(surface)))
                continue

            # Handle kanji parts
            on_readings, kun_readings = ExpressionFilter.get_kanji_readings_jamdict(surface)
            all_readings = on_readings + kun_readings

            if not all_readings:
                continue

            # Find the best reading match for this token
            best_match_score = 0
            best_match_positions = set()

            for reading in all_readings:
                if reading in reading_form:
                    # Score based on reading length and how well it fits
                    match_score = len(reading) * 2

                    # Find all positions where this reading appears
                    start_pos = reading_form.find(reading)
                    if start_pos != -1:
                        positions = set(range(start_pos, start_pos + len(reading)))

                        # Bonus if this doesn't overlap with already matched parts
                        if not positions.intersection(reading_coverage):
                            match_score += len(reading)  # Non-overlapping bonus

                        if match_score > best_match_score:
                            best_match_score = match_score
                            best_match_positions = positions

            # Apply the best match for this token
            alignment_score += best_match_score
            reading_coverage.update(best_match_positions)

        # Bonus for high reading coverage
        if reading_form:
            coverage_ratio = len(reading_coverage) / len(reading_form)
            alignment_score += coverage_ratio * 10

        return alignment_score


    @staticmethod
    def _check_match_reading_substring(test, reading_form, start, end) -> bool:
        if len(reading_form) < start or len(reading_form) < end:
            return False

        substring = reading_form[start:end]
        if substring == test:
            return True

        return False


    @staticmethod
    def get_kanji_readings_jamdict(kanji_char: str) -> Optional[Tuple[List[str], List[str]]]:
        jmd = jamdict.Jamdict()
        result = jmd.lookup(kanji_char)
        if not result:
            return [], []

        result_dict = result.to_dict()
        char_entries = result_dict.get('chars', {})

        if len(kanji_char) > 1:
            kana_readings = []
            try:
                for entry in result_dict.get("entries", []):
                    kana_entries = entry.get('kana', '')
                    for kana_entry in kana_entries:
                        kana_text = kana_entry.get('text', '')
                        kana_text = KanjiUtils.clean_reading(kana_text)
                        kana_text = jaconv.hira2kata(kana_text)
                        kana_readings.append(kana_text)
            except Exception:
                return [], []

            return kana_readings, []

        on_readings = []
        kun_readings = []

        for entry in char_entries:
            literal = entry.get('literal', '')
            if literal != kanji_char:
                continue

            reading_entries = entry.get('rm', [])[0].get('readings', [])
            for reading_entry in reading_entries:
                reading_type = reading_entry.get('type', '')
                reading_value = reading_entry.get('value', '')
                reading_value = KanjiUtils.clean_reading(reading_value)
                reading_value = jaconv.hira2kata(reading_value)

                if reading_value and reading_type == "ja_on":
                    on_readings.append(reading_value)

                if reading_value and reading_type == "ja_kun":
                    kun_readings.append(reading_value)

        return on_readings, kun_readings


if __name__ == "__main__":
    kanji_test_cases = [
        ['アトヲ暗マカス', 'アトヲ暗マス', 'アトヲ暗ム', '暗', '暗マス', '暗ム', '跡', '跡ヲ', '跡ヲクラマカス', '跡ヲクラマス', '跡ヲクラム', '跡ヲ暗マカス', '跡ヲ暗マス', '跡ヲ暗ム'],
        ['雑司ケ谷', '雑司ケ谷ノ', '雑司ケ谷ノキシモジン', '雑司ケ谷ノ鬼子母神', '鬼子母神', 'ゾウシガヤノ鬼子母神'],
        ['インニ篭ル', 'インニ籠ル', '篭ル', '籠', '籠モル', '籠ル', '陰', '陰ニ', '陰ニコモル', '陰ニ篭ル',
         '陰ニ籠モル', '陰ニ籠ル'],
        ['メイワノ変', '変', '明和', '明和ノ', '明和ノヘン', '明和ノ変'],
        ['ツチノ牢', '土', '土ノ', '土ノヒトヤ', '土ノロウ', '土ノ牢', '地', '地ノ', '地ノヒトヤ', '地ノロウ', '地ノ牢',
         '牢'],
        ['バンリイチジョウノ鉄', 'バンリ一条ノテツ', 'バンリ一条ノ鉄', 'バンリ一条鉄', '一', '万里',
         '万里イチジョウテツ', '万里イチジョウノテツ', '万里イチジョウノ鉄', '万里一条', '万里一条ノ', '万里一条ノテツ',
         '万里一条ノ鉄', '万里一条鉄', '条ノ', '条鉄', '鉄'],
        ['アサハラニ茶漬', 'アサハラノ茶漬', '朝腹', '朝腹ニ', '朝腹ニチャ', '朝腹ニチャヅケ', '朝腹ニ茶漬', '朝腹ノ',
         '朝腹ノチャ', '朝腹ノチャヅケ', '朝腹ノ茶漬', '茶漬'],
        ['オキツ荒磯', '奥ツ', '奥ツ荒磯', '沖', '沖ツ', '沖ツアリソ', '沖ツ荒磯', '荒磯'],
        ['ルスヲ預カル', '留主', '留主ヲ', '留主ヲ預カル', '留守', '留守ヲ', '留守ヲアズカル', '留守ヲ預カル',
         '預カル'],
        ['アトミノチャノ湯', 'アトミノ茶', 'アトミノ茶ノユ', 'アトミノ茶ノ湯', 'アトミノ茶事', '湯', '茶', '茶ノ',
         '茶ノ湯', '茶事', '跡見', '跡見ノ', '跡見ノチャ', '跡見ノチャジ', '跡見ノチャノ', '跡見ノチャノユ',
         '跡見ノチャノ湯', '跡見ノ茶', '跡見ノ茶ノユ', '跡見ノ茶ノ湯', '跡見ノ茶事'],
        ['ハナニ嵐', 'ハナニ風', '嵐', '花', '花ニ', '花ニアラシ', '花ニカゼ', '花ニ嵐', '花ニ風', '英', '英ニ',
         '英ニアラシ', '英ニカゼ', '英ニ嵐', '英ニ風', '華', '華ニ', '華ニアラシ', '華ニカゼ', '華ニ嵐', '華ニ風', '風'],
        ['オ江戸', 'ハナノオ江戸', 'ハナノ江戸', '江戸', '花ノ', '花ノエド', '花ノオエド', '花ノオ江戸', '花ノ江戸',
         '英', '英ノ', '英ノエド', '英ノオエド', '英ノオ江戸', '英ノ江戸', '華', '華ノ', '華ノエド', '華ノオエド',
         '華ノオ江戸', '華ノ江戸'],
        ['ニシノミヤノ忌篭', 'ニシノミヤノ忌籠', '忌篭', '忌籠', '西宮', '西宮ノ', '西宮ノイゴモリ', '西宮ノ忌篭',
         '西宮ノ忌籠'],
    ]

    reading_test_cases = [
        ['アト', 'アトヲ', 'アトヲクラマカス', 'アトヲクラマス', 'アトヲクラム', 'カス', 'クラマ', 'クラマス', 'クラム', 'マカス'],
        ['ウシ', 'ウシガ', 'ゾ', 'ゾウシガヤノキシモジン', 'ノキシ', 'モジ', 'モジン', 'ヤノ', 'ヤノキシ'],
        ['インニ', 'インニコモル', 'コモル'],
        ['ヘン', 'メイワ', 'メイワノ', 'メイワノヘン'],
        ['ツチ', 'ツチノ', 'ツチノヒトヤ', 'ツチノロウ', 'ヒト', 'ヒトヤ', 'ロウ'],
        ['イチ', 'ジ', 'テツ', 'バンリ', 'バンリイチジョウテツ', 'バンリイチジョウノテツ', 'ョウ', 'ョウノ'],
        ['アサ', 'アサハラニチャヅケ', 'アサハラノチャヅケ', 'ヅケ', 'ハラ', 'ハラニ', 'ハラニチャ', 'ハラノ',
         'ハラノチャ'],
        ['アリ', 'オキツ', 'オキツアリソ', 'ソ'],
        ['アズカル', 'ルスヲ', 'ルスヲアズカル'],
        ['アト', 'アトミノチャ', 'アトミノチャジ', 'アトミノチャノユ', 'ジ', 'ミノ', 'ミノチャ', 'ミノチャノ', 'ユ'],
        ['アラシ', 'カゼ', 'ハナ', 'ハナニ', 'ハナニアラシ', 'ハナニカゼ'],
        ['エド', 'オエド', 'ハナ', 'ハナノ', 'ハナノエド', 'ハナノオエド'],
        ['イ', 'ゴ', 'ニシ', 'ニシノミヤノ', 'ニシノミヤノイゴモリ', 'モリ']
    ]

    count = 1
    for kanji_forms, reading_forms in zip(kanji_test_cases, reading_test_cases):
        results = ExpressionFilter.filter_full_forms(kanji_forms, reading_forms)
        print(f"\n---- Test case {count} ----")
        for kanji, reading in results:
            print(f"  {kanji} -> {reading}")

        count += 1

