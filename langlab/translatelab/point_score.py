import string
from sentence_splitter import split_text_into_sentences

test = [
"Unlike the other indices, the ARI, along with the Coleman–Liau, relies on a factor of characters per word, instead of the usual syllables per word. Although opinion varies on its accuracy as compared to the syllables/word and complex words indices, characters/word is often faster to calculate, as the number of characters is more readily and accurately counted by computer programs than syllables. In fact, this index was designed for real-time monitoring of readability on electric typewriters",
"We’ve spent a lot of time and energy over the last few years trying to parse the evolution (or whatever you want to call it) of fandom, as passions, parasocial relationships, and good-old-fashioned “being a dick” have all collided in the constantly mutating cauldron that is the internet, often with wholly unpredictable results.",
"The performers at a concert are usually raised above the level of the audience on a stage. Concerts may be held in concert halls which are built for the purpose, or they may be held in any other suitable large building such as a school hall, a nightclub, a barn or a large house or castle. Some concerts are given to very large audiences in the open air. They may take place in a field or in a stadium. The music for these “open-airs” is usually amplified by loudspeakers so that large audiences can hear it.",
"Emerging from behind a cloud blind in a blaze orange miter and camouflaged vestments, His Holiness Pope Francis reportedly celebrated with fellow clergymen Thursday after bagging a highly coveted prize in this year’s Vatican seraphim hunt: a six-winged trophy angel."
]


class PointScore:
    """
    This is the algorithm calculating the point score of tasks.
    Procedure:
        The word count is the basis for the score.
        To measure the complexity of the text, a LIX is calculated. This is a number value, derived from the number
            of words and sentences, and the percentage of long words (more than six characters), in the text. Higher
            is more complex.
        The LIX is normalized out: (lix + normalizing_factor) / 2
            This is to prevent the LIX from changing the point score too much. The factor can be set when instantiating
            the class. Default: 50
        Tasks can have a priority set. This is calculated into the point score. Default parameter: 3.
            1 is very low (0.5), 2 is low (0.75), 3 is normal (1), 4 is high (1.25), 5 is very high (1.5).
        The number is rounded off to become the final score. Minimum score is 10 points.

    Language can also be set as a parameter. This is used for splitting the sentences. Default: 'en'

    Get score by calling obj.score()
    """
    def __init__(self, text, priority=3, normalizing_factor=50, language='en'):
        self.version = 1
        self.text = text
        self.language = language
        self.normalizing_factor = normalizing_factor
        self.priority = priority
        self.priority_factor = {
            1: 0.5,
            2: 0.75,
            3: 1,
            4: 1.25,
            5: 1.5
        }
        self.word_count = 0
        self._long_words_count = 0
        self._sentence_count = 0
        self._count_it_up()

    def _count_it_up(self):
        sentences = split_text_into_sentences(text=self.text, language=self.language)
        sentence_count = len(sentences)
        words = []

        for sentence in sentences:
            sentence_stripped = sentence.translate(str.maketrans('', '', string.punctuation))
            words += sentence_stripped.split()

        long_words_count = 0
        for word in words:
            if len(word) >= 7:
                long_words_count += 1

        self.word_count = len(words)
        self._sentence_count = sentence_count
        self._long_words_count = long_words_count

    def lix(self):
        lix = self.word_count / self._sentence_count + (100 * self._long_words_count) / self.word_count
        return lix

    def score(self):
        lix = self.lix()
        scaling_factor = ((lix + self.normalizing_factor) / 2) * 0.02  # could probably be made more efficient
        score = self.word_count * scaling_factor
        int_score = int(score)
        if int_score < 10:
            int_score = 10
        if self.priority_factor.get(self.priority, None):
            int_score = int_score * self.priority_factor[self.priority]
        return int_score

    def __str__(self):
        return str(self.score())
