# -*- coding: utf-8 -*-
import json

age = {
    'Select...': None,
    '25-30': '25-29',
    'Over 50': 'Over 50',
    'Select...': None,
    '35-40': '35-39',
    '40-44': '40-44',
    '30-34': '30-34',
    '22-24': '22-24',
    '18-21': '18-21',
    'Under 18': 'under 18',
    '45-50': '45-49',
    'Prefer not to answer': None
}

education = {
    'Some (or attending) graduate school': 'some or attending graduate or professional school',
    'Four-year college degree': '4-year college degree',
    'Graduate degree': 'graduate or professional degree',
    'Select...': None,
    'High school': 'high school diploma or GED',
    'Not applicable': 'not applicable - no spouse or partner',
    'Two-year college degree': '2-year college degree',
    'Some (or attending) college': 'some or attending college',
    'Some (or attending) high school': 'some or attending high school',
    'Prefer not to answer': None,
     u'Baz\u0131 (veya kat\u0131l\u0131yor) \xfcniversite': 'some ore attending college'
}

gender = {
    'Male': 'male',
    'Female': 'female',
    'Select...': None,
    'Other': 'other',
    u'Kad\u0131n': None,
    'Prefer not to answer': 'prefer not to answer'
}

child_genders = {
    'male': 'male',
    'female': 'female',
    'other': 'other or prefer not to answer'
}

guardiansNumber = {
    "2": '2',
    "1  ": '1',
    "": None,
    "4 (lives with parents and paternal grandparents)": '4',
    "1": '1',
    "0": '0',
    "Two": '2',
    "two": '2',
    "3": '3',
    "2 (My son lives with both parents, and my daughters live with both parents and step-dad.": '2',
    "one": '1',
    "2 plus grandparents": '2',
    "2, one of our children spends time with her mother as well": '2',
    "2 but mother and father live with one set of child's grandparents who love caring for him": '2',
    "original mother & father living together with a child": '2',
    "shared custody for both, 2 fathers": '1',
    "6": '6',
    "4": '4',
    "Mother/Father": '2',
    "Three": '3',
    "five": '5',
    "1 at a time": '1',
    "2 mother and father": '2',
    "5": '5',
    "2 (have 50/50 custody of older boy)": '2',
    "3, we live in a family home.": '3',
    "2; coparent- separate homes": '2',
    "one-me": '1',
    "Both": '2',
    "03/27/2010": None,
    "both Mom and Dad": '2',
    "1 (and one non-guardian)": '1',
    "22": '22',
    "2, 1": '1',
    "My oldest lives wih me and goes to her biological dad every other weekend. My youngest lives with me": '1',
    "both": '2',
    "mother (24) and": None,
    "One": '1',
    "2 parents": '2',
    "usually 1 my partner travels for work": '1',
    "the 2 eldest live with a pair of grandparents and the youngest lives with me": '1',
    "Both parents": '2',
    "04/2011/15": None
}

guardiansExp = {
    "2": '',
    "1  ": '',
    "": '',
    "4 (lives with parents and paternal grandparents)": 'lives with parents and paternal grandparents',
    "1": '',
    "0": '',
    "Two": '',
    "two": '',
    "3": '',
    "2 (My son lives with both parents, and my daughters live with both parents and step-dad.": 'My son lives with both parents, and my daughters live with both parents and step-dad.',
    "one": '',
    "2 plus grandparents": '2 plus grandparents',
    "2, one of our children spends time with her mother as well": 'one of our children spends time with her mother as well',
    "2 but mother and father live with one set of child's grandparents who love caring for him": 'but mother and father live with one set of child\'s grandparents who love caring for him',
    "original mother & father living together with a child": '',
    "shared custody for both, 2 fathers": 'shared custody for both, 2 fathers',
    "6": '',
    "4": '',
    "Mother/Father": '',
    "Three": '',
    "five": '',
    "1 at a time": '1 at a time',
    "2 mother and father": '',
    "5": '',
    "2 (have 50/50 custody of older boy)": 'have 50/50 custody of older boy',
    "3, we live in a family home.": 'we live in a family home.',
    "2; coparent- separate homes": 'coparent- separate homes',
    "one-me": '',
    "Both": '',
    "03/27/2010": '',
    "both Mom and Dad": '',
    "1 (and one non-guardian)": 'and one non-guardian',
    "22": '',
    "2, 1": '2/1/2016',
    "My oldest lives wih me and goes to her biological dad every other weekend. My youngest lives with me": 'My oldest lives wih me and goes to her biological dad every other weekend. My youngest lives with me',
    "both": '',
    "mother (24) and": 'mother (24) and',
    "One": '',
    "2 parents": '',
    "usually 1 my partner travels for work": 'usually 1 my partner travels for work',
    "the 2 eldest live with a pair of grandparents and the youngest lives with me": 'the 2 eldest live with a pair of grandparents and the youngest lives with me',
    "Both parents": '',
    "04/2011/15": ''
}

race = {"": [], "african american/puerto rican": ["Hispanic, Latino, or Spanish origin", "Black or African American"], "Horse": [], "White/European": ["White"], "Japanese, Korean and African American.": ["Black or African American", "Asian"], "White- Hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "Multi racial (white and black)": ["White", "Black or African American"], "black/caucasion": ["White", "Black or African American"], "white hispanic and black": ["White", "Hispanic, Latino, or Spanish origin", "Black or African American"], "hispanic, white": ["White", "Hispanic, Latino, or Spanish origin"], "Chinese and Caucasian": ["White", "Asian"], "white european": ["White"], "Black,White": ["White", "Black or African American"], "Mixed, Asian dad and White mom": ["White", "Asian"], "asian": ["Asian"], "human": [], "Indian-American": ["Asian"], "Prefer not to answer": [], "Hispanic, Caucasian": ["White", "Hispanic, Latino, or Spanish origin"], "White": ["White"], "White/Latino": ["White", "Hispanic, Latino, or Spanish origin"], "Black and White": ["White", "Black or African American"], "Indian,Carribean": ["Black or African American", "Asian"], "European": ["White"], "ehite": ["White"], "white/hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "black american": ["Black or African American"], "American/ white": ["White"], "south asian": ["Asian"], "Black and Native American": ["Black or African American", "American Indian or Alaska Native"], "Caucasian/Hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "white and mexican": ["White", "Hispanic, Latino, or Spanish origin"], "Caucasian, Korean": ["White", "Asian"], "Indian Origin": ["Asian"], "white/ Puerto Rican": ["White", "Hispanic, Latino, or Spanish origin"], "spanish": ["Hispanic, Latino, or Spanish origin"], "black": ["Black or African American"], "white and black": ["White", "Black or African American"], "Caucasion": ["White"], "Caucasian, Hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "Caucasian/African American": ["White", "Black or African American"], "African-America": ["Black or African American"], "White and proud of it": ["White"], "Black/African-American": ["Black or African American"], "Ashkenazi Jewish": ["Another race, ethnicity, or origin"], "biracial": ["Another race, ethnicity, or origin"], "Caucasian/Native American": ["White", "American Indian or Alaska Native"], "Mexican-American": ["Hispanic, Latino, or Spanish origin"], "Mexican/White": ["White", "Hispanic, Latino, or Spanish origin"], "White, Black, Hispanic, Indian": ["White", "Hispanic, Latino, or Spanish origin", "Black or African American", "Asian"], "Caucasian and Biracial": ["White", "Another race, ethnicity, or origin"], "Caucasan": ["White"], "black/ white": ["White", "Black or African American"], "White, Hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "While": ["White"], "white/indian": ["White", "Asian"], "White/Puerto Rican": ["White", "Hispanic, Latino, or Spanish origin"], "White Americans": ["White"], "White, Asiah": ["White", "Asian"], "african american": ["Black or African American"], "Black, White": ["White", "Black or African American"], "hispanic/white": ["White", "Hispanic, Latino, or Spanish origin"], "Irish/Native American": ["White", "American Indian or Alaska Native"], "Caucasian / White": ["White"], "olive tone24": [], "bi racial": ["Another race, ethnicity, or origin"], "human being": [], "White/ Black": ["White", "Black or African American"], "white/asian": ["White", "Asian"], "withe": ["White"], "white / hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "Whie": ["White"], "Caucasian, asian": ["White", "Asian"], "white and native american": ["White", "American Indian or Alaska Native"], "White (son is adopted and half hispanic)": ["White", "Hispanic, Latino, or Spanish origin"], "Puerto Rican": ["Hispanic, Latino, or Spanish origin"], "White/Caucasian": ["White"], "White, American Indian": ["White", "American Indian or Alaska Native"], "WHite": ["White"], "White, hispanic - I\'m 1/4": ["White", "Hispanic, Latino, or Spanish origin"], "italian": ["White"], "African America": ["Black or African American"], "African American/Asian": ["Black or African American", "Asian"], "White and american Indian": ["White", "American Indian or Alaska Native"], "White, Central Asian": ["White", "Asian"], "white, black": ["White", "Black or African American"], "Hispanic / Caucasian": ["White", "Hispanic, Latino, or Spanish origin"], "American, Filipino, Native American": ["White", "Asian", "American Indian or Alaska Native"], "Caucasian and asian": ["White", "Asian"], "cacasion": ["White"], "Caucasian/white": ["White"], "White and Latin": ["White", "Hispanic, Latino, or Spanish origin"], "Asian, White": ["White", "Asian"], "whtie": ["White"], "hindu": ["Asian"], "hispanic, african-american": ["Hispanic, Latino, or Spanish origin", "Black or African American"], "Blk": ["Black or African American"], "White/hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "White, Asian": ["White", "Asian"], "white/ mexican": ["White", "Hispanic, Latino, or Spanish origin"], "South Asian": ["Asian"], "African American, Caucasian": ["White", "Black or African American"], "White and Black": ["White", "Black or African American"], "Hispanic/African american": ["Hispanic, Latino, or Spanish origin", "Black or African American"], "White, Chinese": ["White", "Asian"], "black/hispanic": ["Hispanic, Latino, or Spanish origin", "Black or African American"], "black, caucasian": ["White", "Black or African American"], "Causasian": ["White"], "jamaican, chinese, indian": ["Black or African American", "Asian"], "White/mixed": ["White", "Another race, ethnicity, or origin"], "Black/White": ["White", "Black or African American"], "Jewish?": ["Another race, ethnicity, or origin"], "indian": ["Asian"], "blk": ["Black or African American"], "Caucasioan": ["White"], "bla CV k": ["Black or African American"], "African american": ["Black or African American"], "America": [], "caucasian": ["White"], "Mixed Puerto Rican & Irish": ["White", "Hispanic, Latino, or Spanish origin"], "white/Hispanic": ["White"], "None": [], "Asian and White": ["White", "Asian"], "Native American": ["American Indian or Alaska Native"], "White (Non-Hispanic)": ["White"], "Caucasian / Mixed": ["White", "Another race, ethnicity, or origin"], "White and Native American": ["White", "American Indian or Alaska Native"], "Hispanic and white": ["White", "Hispanic, Latino, or Spanish origin"], "White and Hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "middle eastern": ["Middle Eastern or North African"], "white not hispanic": ["White"], "Caucasian / Asian": ["White", "Asian"], "African": ["Black or African American"], "Mixed": ["Another race, ethnicity, or origin"], "w": ["White"], "White and Filipino": ["White", "Asian"], "black and white": ["White", "Black or African American"], "White (Cacausian)": ["White"], "Hispanic; White": ["White", "Hispanic, Latino, or Spanish origin"], "Multiracial": ["Another race, ethnicity, or origin"], "wite": ["White"], "whote": ["White"], "WHITE/ASIAN": ["White", "Asian"], "Chinese": ["Asian"], "black and asian": ["Black or African American", "Asian"], "native american and white": ["White", "American Indian or Alaska Native"], "Caucasian and Asian": ["White", "Asian"], "Hispaic": ["Hispanic, Latino, or Spanish origin"], "Mexican American": ["Hispanic, Latino, or Spanish origin"], "African American, Mexican American": ["Hispanic, Latino, or Spanish origin", "Black or African American"], "White and Middle Eastern": ["White", "Middle Eastern or North African"], "Caucasian and black": ["White", "Black or African American"], "american": [], "Americans": [], "Hispanic / caucasian": ["White", "Hispanic, Latino, or Spanish origin"], "Hispanic Caucasian": ["White", "Hispanic, Latino, or Spanish origin"], "mixed": ["Another race, ethnicity, or origin"], "Asian or Pacific Islander": ["Asian"], "white/Caucasian, both Hispanic and not Hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "Caucasian (non-Hispanic)": ["White"], "White and Asian": ["White", "Asian"], "WHITE/HISPANIC": ["White", "Hispanic, Latino, or Spanish origin"], "White, Korean": ["White", "Asian"], "african american and hispanic": ["Hispanic, Latino, or Spanish origin", "Black or African American"], "Puertorican": ["Hispanic, Latino, or Spanish origin"], "Hispanic /Caucasian": ["White", "Hispanic, Latino, or Spanish origin"], "African american and hispanic": ["Hispanic, Latino, or Spanish origin", "Black or African American"], "hispanic, caucasion": ["White", "Hispanic, Latino, or Spanish origin"], "Multi Racial": ["Another race, ethnicity, or origin"], "whighe": ["White"], "mixes Races": ["Another race, ethnicity, or origin"], "White/Black": ["White", "Black or African American"], "white, hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "Hispanic/Caucasian": ["White", "Hispanic, Latino, or Spanish origin"], "Indian": ["Asian"], "Black": ["Black or African American"], "Biracial, Mexican and White": ["White", "Hispanic, Latino, or Spanish origin"], "muslim": [], "White/Caucasion": ["White"], "Korean": ["Asian"], "South Asian (Indian)": ["Asian"], "Other": ["Another race, ethnicity, or origin"], "caucasain": ["White"], "white/native american": ["White", "American Indian or Alaska Native"], "Asian, caucasian": ["White", "Asian"], "Asian American/Caucasion": ["White", "Asian"], "White/Hispanic (Puerto Rican)": ["White", "Hispanic, Latino, or Spanish origin"], "Black or African American": ["Black or African American"], "FILIPINO": ["Asian"], "African-American": ["Black or African American"], "whitw": ["White"], "NA": [], "South East Asian": ["Asian"], "Hispanic-White": ["White", "Hispanic, Latino, or Spanish origin"], "White/black": ["White", "Black or African American"], "White (mom is half-Cuban)": ["White", "Hispanic, Latino, or Spanish origin"], "2": [], "ASIAN": ["Asian"], "cacasuon": ["White"], "Korean, German, Italian": ["White", "Asian"], "white": ["White"], "Hispanic and White": ["White", "Hispanic, Latino, or Spanish origin"], "Asian / White": ["White", "Asian"], "Black and white": ["White", "Black or African American"], "white/caucasian": ["White"], "Mixed-racial": ["Another race, ethnicity, or origin"], "white and hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "indian, black, and creole": ["Black or African American", "Asian"], "Asian, Latino/multi-ethnic, and multi-ethnic": ["Hispanic, Latino, or Spanish origin", "Asian", "Another race, ethnicity, or origin"], "Latino": ["Hispanic, Latino, or Spanish origin"], "White; Natiive American": ["White", "American Indian or Alaska Native"], "black and hispanic": ["Hispanic, Latino, or Spanish origin", "Black or African American"], "White/Caucasian/German, English, Irish, and Polish Decent": ["White"], "White / Hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "American": [], "caucasion": ["White"], "white & mixed": ["White", "Another race, ethnicity, or origin"], "African American": ["Black or African American"], "African America/Caucasian": ["White", "Black or African American"], "Hispanic/White": ["White", "Hispanic, Latino, or Spanish origin"], "Asya": ["Asian"], "Black/White/Bi-racial": ["White", "Black or African American"], "Hispanic American": ["Hispanic, Latino, or Spanish origin"], "White/Hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "Asian/American": ["White", "Asian"], "White, Black": ["White", "Black or African American"], "cambodian/caucasian": ["White", "Asian"], "African Amercian": ["Black or African American"], "Black/Japanese": ["Black or African American", "Asian"], "White/American Indian": ["White", "American Indian or Alaska Native"], "african american, white, american indian": ["White", "Black or African American", "American Indian or Alaska Native"], "Caucasian, Hispanic, Native American": ["White", "Hispanic, Latino, or Spanish origin", "American Indian or Alaska Native"], "Columbia American": ["Hispanic, Latino, or Spanish origin"], "White, black, latino": ["White", "Hispanic, Latino, or Spanish origin", "Black or African American"], "interracial": ["Another race, ethnicity, or origin"], "I\'m Chinese American, and my partner is Caucasian.": ["White", "Asian"], "puerto rican": ["Hispanic, Latino, or Spanish origin"], "italain and irish": ["White"], "Hispanic and German": ["White", "Hispanic, Latino, or Spanish origin"], "black/african american": ["Black or African American"], "Caucasin": ["White"], "Korean, White": ["White", "Asian"], "mexican , caucasian": ["White", "Hispanic, Latino, or Spanish origin"], "German": ["White"], "Mixed race": ["Another race, ethnicity, or origin"], "White, Afro-Brazilian": ["White", "Black or African American"], "Multi-Racial, Black, White, Hawaiian": ["White", "Black or African American", "Native Hawaiian or Other Pacific Islander"], "Chinese/Albanian": ["White", "Asian"], "Vietnamese": ["Asian"], "white,asian (japanese + indian)": ["White", "Asian"], "White,  Black": ["White", "Black or African American"], "white/mexican": ["White", "Hispanic, Latino, or Spanish origin"], "White/Filipino": ["White", "Asian"], "black,mexican": ["Hispanic, Latino, or Spanish origin", "Black or African American"], "Caucasian, Asian": ["White", "Asian"], "Black American": ["Black or African American"], "White/ black": ["White", "Black or African American"], "BLACK": ["Black or African American"], "Native American, Asian, White": ["White", "Asian", "American Indian or Alaska Native"], "Australian": ["White"], "White, mexican": ["White", "Hispanic, Latino, or Spanish origin"], "Caucasian": ["White"], "Native American/Pacific Islander": ["American Indian or Alaska Native"], "african american, hispanic, caucasion": ["White", "Hispanic, Latino, or Spanish origin", "Black or African American"], "african american and caucasian": ["White", "Black or African American"], "Asian American": ["Asian"], "White/Asian": ["White", "Asian"], "asian/white": ["Asian"], "Pakistani": ["Asian"], "Mixed asian and white": ["White", "Asian"], "Chicano": ["Hispanic, Latino, or Spanish origin"], "Multi raced": ["Another race, ethnicity, or origin"], "Blk/wht": ["White", "Black or African American"], "caucasian, step daughter\'s mother\'s side identifies as chicano": ["White", "Hispanic, Latino, or Spanish origin"], "1": [], "White, Mexican": ["White", "Hispanic, Latino, or Spanish origin"], "alaskan native, white": ["White", "American Indian or Alaska Native"], "other": ["Another race, ethnicity, or origin"], "5": [], "African Native AMERICAN, HISPANIC": ["Hispanic, Latino, or Spanish origin", "Black or African American", "American Indian or Alaska Native"], "White/spanish": ["White", "Hispanic, Latino, or Spanish origin"], "Mix race : Black and white": ["White", "Black or African American"], "White / African American": ["White", "Black or African American"], "latino": ["Hispanic, Latino, or Spanish origin"], "Hispanic/latino": ["Hispanic, Latino, or Spanish origin"], "Mexican and Asian": ["Hispanic, Latino, or Spanish origin", "Asian"], "White and black": ["White", "Black or African American"], "african American": ["Black or African American"], "Human": [], "africanAmerican": ["Black or African American"], "Caucasian and Hispanic": ["White", "Hispanic, Latino, or Spanish origin"], "causasian": ["White"], "white/black": ["White", "Black or African American"], "White, Black, Latin": ["White", "Hispanic, Latino, or Spanish origin", "Black or African American"], "Egyptian father. white mom": ["White", "Middle Eastern or North African"], "sikh": [], "Hispanic, White": ["White", "Hispanic, Latino, or Spanish origin"], "white american": ["White"], "WHITE": ["White"], "White, Black, Hispanic": ["White", "Hispanic, Latino, or Spanish origin", "Black or African American"], "Caucasian/Asian": ["White", "Asian"], "native american": ["American Indian or Alaska Native"], "white and Asian": ["White", "Asian"], "Mexican": ["Hispanic, Latino, or Spanish origin"], "White British": ["White"], "biracial (asian and black)": ["Black or African American", "Asian"], "Hispanic": ["Hispanic, Latino, or Spanish origin"], "Peruvian": ["Hispanic, Latino, or Spanish origin"], "Mixed- White and Black": ["White", "Black or African American"], "White, Black, Mixed": ["White", "Black or African American"], "White (Mom), Black (Dad), Biracial (Son)": ["White", "Black or African American"], "white, african american": ["White", "Black or African American"], "multiracial": ["Another race, ethnicity, or origin"], "hispanic": ["Hispanic, Latino, or Spanish origin"], "Whate": ["White"], "Asian": ["Asian"], "Caucasian; African": ["White", "Black or African American"], "AFRICAN AMERICAN": ["Black or African American"], "Alaska Native and White": ["White", "American Indian or Alaska Native"], "white cuacasian": ["White"], "Caucausian": ["White"], "Mother White/Non-Hispanic, Father White/Puerto Rican. Son has not selected a racial identity yet.": ["White", "Hispanic, Latino, or Spanish origin"], "creole, white, hispanic": ["White", "Hispanic, Latino, or Spanish origin", "Black or African American"]}

siblings = {
	"1": '1',
	"0": '0',
	"": None,
	"2": '2',
	"One": '1',
	"4": '4',
	"3": '3',
	"8": '8',
	"5": '5',
	"7": '7',
	"Two": '2',
	"one": '1',
	"three": '3',
	"6": '6',
	"two": '2',
	" 1": '1',
	"9": '9',
	"`1": '1',
	"01": '1',
	"one ": '1',
	"great": None,
	"1.5": '1',
	"10": '10'
}

income = {
    'Select...': None,
    'Over $100000': 'Over $100000',
    '$75000-$100000': '$75000-$100000',
    '$30000-$50000': '$30000-$50000',
    'Under $30000': 'Under $30000',
    '$50000-$75000': '$50000-$75000',
    'Prefer not to answer': 'prefer not to answer',
    u'30.000 $ alt\u0131nda': 'Under $30000'
}

siblingAges = json.load(open('ages.json', 'r'))

MAPPINGS = {
    'age': {
        'ref': age,
        'to': 'demographicsAge'
    },
    'education-you': {
        'ref': education,
        'to': 'demographicsEducationLevel'
    },
    'education-spouse': {
        'ref': education,
        'to': 'demographicsSpouseEducationLevel'
    },
    'gender': {
        'ref': gender,
        'to': 'demographicsGender'
    },
    'guardians': [
        {
            'ref': guardiansNumber,
            'to': 'demographicsNumberOfGuardians'
        }, {
            'ref': guardiansExp,
            'to': 'demographicsNumberOfGuardiansExplanation'
        }
    ],
    'language': {
        'to': 'demographicsLanguagesSpokenAtHome'
    },
    'race': {
        'ref': race,
        'to': 'demographicsRaceIdentification'
    },
    'siblings': {
        'ref': siblings,
        'to': 'demographicsNumberOfChildren'
    },
    'family-income': {
        'ref': income,
        'to': 'demographicsAnnualIncome'
    },
    'comments': {
        'to': 'demographicsAdditionalComments'
    },
    'siblingages': {
        'to': 'demographicsChildBirthdays',
        'ref': siblingAges
    }
}
