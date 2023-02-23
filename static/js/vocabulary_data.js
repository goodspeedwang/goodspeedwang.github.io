const DATA = [
    {
        explanation: "to praise something or someone very much",
        test:
        {
            word: "extol",
            sentence: "Though they extol the virtues of the peaceful life, only one of them has ever gone to live in the country and he was back in town within six months. Even he still lives under the illusion that country life is somehow superior to town life."
        }
    },
    {
        explanation: "a good moral quality in a person, or the general quality of being morally good",
        test:
        {
            word: "virtues",
            sentence: "Though they extol the virtues of the peaceful life, only one of them has ever gone to live in the country and he was back in town within six months. Even he still lives under the illusion that country life is somehow superior to town life."
        }
    },
    {
        explanation: "A place or experience is extremely pleasant, beautiful, or peaceful",
        test: {
            word: "idyllic",
            sentence: "This idyllic pastoral scene is only part of the picture."
        }
    }, {
        explanation: "to deal with something unpleasant or annoying, or to continue existing despite bad or difficult conditions",
        test: {
            word: "tolerate",
            sentence: "Why people are prepared to tolerate a four-hour journey each day for the dubious privilege of living in the country is beyond me."
        }
    },
    {
        explanation: "unusual and exciting because of coming (or seeming to come) from far away, especially in a tropical country",
        test: {
            word: "exotic",
            sentence: "stagger home loaded with as many of the exotic items as they can carry."
        }
    },
    {
        explanation: "in an unreasonably determined way, especially by acting in a particular way and not changing at all, despite what anyone else says",
        test: {
            word: "obstinately",
            sentence: "It has always been a mystery to me why city dwellers, who appreciate all these things, obstinately pretend that they would prefer to live in the country."
        }
    },
    {
        explanation: "the situation of being alone, often by choice",
        test: {
            word: "solitude",
            sentence: "Perhaps it is the desire for solitude or the chance of making an unexpected discovery that lures people down to the depths of the earth."
        }
    },
    {
        explanation: "to allow yourself or another person to have something enjoyable, especially more than is good for you",
        test: {
            word: "indulge",
            sentence: "Inviting the fire brigade to put out a nonexistent fire is a crude form of deception which no self-respecting student would ever indulge in"
        }
    },

    {
        explanation: "in a frightening, violent, or powerful way",
        test: {
            word: "fiercely",
            sentence: "the workmen struggled fiercely."
        }
    },

    {
        explanation: "to take using sudden force",
        test: {
            word: "seize",
            sentence: "the police attempted to seize the pneumatic drill."
        }
    },
    {

        explanation: "a very large rock",
        test: {
            word: "boulders",
            sentence: "the road was littered with boulders."
        }
    }, {
        explanation: "to change direction, especially suddenly",
        test: {
            word: "swerved",
            sentence: "we swerved to avoid large boulders."
        }
    }, {
        explanation: "in a way that suggests that something unpleasant is likely to happen",
        test: {
            word: "ominously",
            sentence: "The wheels scooped up stones that hammered ominously under the car."
        }
    }, {
        explanation: "to move something with a scoop or with something used as a scoop",
        test: {
            word: "scooped",
            sentence: "The wheels scooped up stones that hammered ominously under the car."
        }
    }, {
        explanation: "a line or pattern that looks like a Z or a row of Zs joined together",
        test: {
            word: "zigzag",
            sentence: "He followed its zigzag course."
        }
    },
    {
        explanation: "to look at or consider a person or thing carefully and in detail in order to discover something about them",
        test: {
            word: "examine",
            sentence: "We saw Bruce remaining in the car when we all got out to examine the fissure."
        }
    },
    {
        explanation: "causing you to have fear or respect for something or someone because that thing or person is large, powerful, or difficult",
        test: {
            word: "formidable",
            sentence: "most of us could compile formidable lists of dos and don'ts"
        }
    },
    {
        explanation: "someone who does something very often and cannot stop doing it",
        test: {
            word: "inveterate",
            sentence: "if we remain inveterate smokers, it is only because we have so often experienced the frustration that results from failure."
        }
    }, {
        explanation: "in a way that involves great care and attention to detail",
        test: {
            word: "assiduously",
            sentence: "On the second, I applied myself assiduously to the task."
        }
    }, {
        explanation: "the ability to control yourself or other people, even in difficult situations",
        test: {
            word: "discipline",
            sentence: "The self-discipline required to drag myself out of bed eleven minutes earlier than usual was considerable."
        }
    }, {
        explanation: "unkind remarks made to intentionally annoy and upset someone",
        test: {
            word: "taunts",
            sentence: "I fended off the taunts and jibes of the family good-humouredly."
        }
    }, {
        explanation: "to keep your attention so strongly that you feel unable to move or look away",
        test: {
            word: "hypnotizing",
            sentence: "Resisting the hypnotizing effect of television, I sat in my room for a few evenings with my eyes glued to a book."
        }
    }, {
        explanation: "you start to sleep, especially during the day",
        test: {
            word: "dozing",
            sentence: "I soon got back to my old bad habit of dozing off in front of the television."
        }
    },
    {
        explanation: "a subject or activity that interests you very much",
        test: {
            word: "enthusiasm",
            sentence: "However, my enthusiasm waned."
        }
    },
    {
        explanation: "to try to do or continue doing something in a determined but often unreasonable way",
        test: {
            word: "persisted",
            sentence: "she persisted in living long after her husband's death."
        }
    },
    {
        explanation: "in a way that is expensive or impressive",
        test: {
            word: "lavishly",
            sentence: "Before she grew old, Aunt Harriet used to entertain lavishly."
        }
    },
    {
        explanation: "perfectly clean or tidy",
        test: {
            word: "immaculate",
            sentence: "No matter how many guests were present, the great house was always immaculate."
        }
    },
    {
        explanation: "in a way that is very surprising or difficult to believe",
        test: {
            word: "miraculously",
            sentence: "Even my uncle's huge collection of books was kept miraculously free from dust."
        }
    },
    {
        explanation: "to try to achieve",
        test: {
            word: "pursued",
            sentence: "Though my aunt pursued what was, in those days, an enlightened policy, in that she never allowed her domestic staff to work more than eight hours a day, she was extremely difficult to please."
        }
    },
    {
        explanation: "the quality of being likely to change suddenly and without warning",
        test: {
            word: "fickleness",
            sentence: "While she always criticized the fickleness of human nature, "
        }
    },
    {
        explanation: "laughter, humor, or happiness",
        test: {
            word: "mirth",
            sentence: "Though this caused great mirth among the guests, Aunt Harriet was horrified."
        }
    },
    {
        explanation: "to be in charge of a formal meeting, ceremony, or trial",
        test: {
            word: "presided",
            sentence: "Aunt Harriet presided over an invisible army of servants that continuously scrubbed, cleaned, and polished."
        }
    },
    {
        explanation: "not in the place where you are expected to be, especially at school or work",
        test: {
            word: "absent",
            sentence: "After being absent from The Gables for a week, my aunt unexpectedly returned one afternoon with a party of guests and instructed Bessie to prepare dinner."
        }
    },
    {
        explanation: "an ability, characteristic, or experience that makes you suitable for a particular job or activity",
        test: {
            word: "qualifications",
            sentence: "In addition to all her other qualifications, Bessie was an expert cook."
        }
    },
    {
        explanation: "a tall cupboard in which you hang your clothes",
        test: {
            word: "wardrobe",
            sentence: "bottles of all shapes and sizes neatly stacked in what had once been Bessie's wardrobe"
        }
    },
    {
        explanation: "relating to the design of buildings",
        test: {
            word: "architectural",
            sentence: "These attracted many tourists, for they were not only of great architectural interest, but contained a large number of beautifully preserved frescoes as well."
        }
    },
    {
        explanation: "to cause people to do or believe something, esp. by explaining why they should",
        test: {
            word: "persuaded",
            sentence: "Though he was reluctant to do so at first, we eventually persuaded him to take us"
        }
    },
    {
        explanation: "unfriendly and likely to be unpleasant or harmful",
        test: {
            word: "forbidding",
            sentence: "Even under a clear blue sky, the village looked forbidding, as all the houses were built of grey mud bricks."
        }
    },
    {
        explanation: "old and in poor condition",
        test: {
            word: "dilapidated",
            sentence: "Sitting down on a dilapidated wooden fence near the field, we opened a couple of tins of sardines and had a picnic lunch."
        }
    },
    {
        explanation: "the amount or number of something, especially that can be measured",
        test:
        {
            word: "quantities",
            sentence: "The need to produce ever-increasing quantities of cheap food leads to a different kind of pollution."
        }
    },
    {
        explanation: "(of something unpleasant or dangerous) gradually and secretly causing harm",
        test:
        {
            word: "insidious",
            sentence: "There is an even more insidious kind of pollution that particularly affects urban areas and invades our daily lives, and that is noise."
        }
    },
    {
        explanation: "农药",
        test:
        {
            word: "pesticides",
            sentence: "The use of pesticides and fertilizers produces cheap grains and vegetables."
        }
    },
    {
        explanation: "肥料",
        test:
        {
            word: "fertilizers",
            sentence: "The use of pesticides and fertilizers produces cheap grains and vegetables."
        }
    },
    {
        explanation: "沙门氏菌",
        test:
        {
            word: "salmonella",
            sentence: "salmonella in chicken and eggs"
        }
    },
    {
        explanation: "in bad condition and therefore weak and likely to break",
        test:
        {
            word: "rickety",
            sentence: "the furniture gets rickety"
        }
    },
    {
        explanation: "to take a machine apart or to come apart into separate pieces",
        test:
        {
            word: "dismantle",
            sentence: "the mower firmly refused to mow, so I decided to dismantle it."
        }
    },
    {
        explanation: "(especially of a problem or a difficulty) so great that it cannot be dealt with successfully",
        test:
        {
            word: "insurmountable",
            sentence: "After buying a new chain I was faced with the insurmountable task of putting the confusing jigsaw puzzle together again."
        }
    },
    {
        explanation: "电工",
        test:
        {
            word: "electrician",
            sentence: "electrician"
        }
    },
    {
        explanation: "木匠",
        test:
        {
            word: "carpenter",
            sentence: "carpenter"
        }
    },
    {
        explanation: "水电工",
        test:
        {
            word: "plumber",
            sentence: "plumber"
        }
    },
    {
        explanation: "机修工",
        test:
        {
            word: "mechanic",
            sentence: "mechanic"
        }
    },
    {
        explanation: "吸尘器",
        test:
        {
            word: "vacuum",
            sentence: "vacuum cleaners fail to operate"
        }
    },
    {
        explanation: "拼图",
        test:
        {
            word: "jigsaw",
            sentence: "putting the confusing jigsaw puzzle together again."
        }
    },
    {
        explanation: "in a way that cannot be avoided",
        test:
        {
            word: "inevitably",
            sentence: "inevitably you arrive at your destination almost exhausted."
        }
    },
    {
        explanation: "to criticize something or someone strongly, usually for moral reasons.",
        test:
        {
            word: "condemned",
            sentence: "In democratic countries, any efforts to restrict the freedom of the press are rightly condemned."
        }
    },
    {
        explanation: "considered too important to be changed",
        test:
        {
            word: "sacred",
            sentence: "acting on the contention that facts are sacred."
        }
    },
    {
        explanation: "any of five children born at the same time to the same mother",
        test:
        {
            word: "quintuplets",
            sentence: "they suddenly became the parents of quintuplets."
        }
    },
    {
        explanation: "摄像机",
        test:
        {
            word: "cameras",
            sentence: "Television cameras and newspapers carried the news to everyone in the country."
        }
    },
    {
        explanation: "a substance or product that can be traded, bought, or sold",
        test:
        {
            word: "commodity",
            sentence: "Instead of being five new family members, these children had become a commodity."
        }
    },
    {
        explanation: "not having enough space or time",
        test:
        {
            word: "cramped",
            sentence: "Train compartments soon get cramped and stuffy."
        }
    },
    {
        explanation: "to do something awkwardly, especially when using your hands",
        test:
        {
            word: "fumbling",
            sentence: "or fumbling to find your ticket for inspection."
        }
    },
    {
        explanation: "巡游船",
        test:
        {
            word: "cruises",
            sentence: "Ferry trips or cruises offer a great variety of civilized comforts."
        }
    },
    {
        explanation: "making you feel very excited and happy",
        test:
        {
            word: "exhilarating",
            sentence: "Traveling at a height of 30000 feet and over 500 miles an hour is an exhilarating experience."
        }
    },
    {
        explanation: "a small change that improves something",
        test:
        {
            word: "refinements",
            sentence: "But even when the refinements are not available, there is plenty to keep you occupied."
        }
    },
    {
        explanation: "not full of folds",
        test:
        {
            word: "uncrumpled",
            sentence: "You will arrive at your destination fresh and uncrumpled."
        }
    },
    {
        explanation: "difficult, needing a lot of effort and energy",
        test:
        {
            word: "arduous",
            sentence: "You will not have to spend the next few days recovering from a long and arduous journey."
        }
    },
]

/*
{
explanation: "",
test: 
{
word: "",
sentence: ""
}
},
*/