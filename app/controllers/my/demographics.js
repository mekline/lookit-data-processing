import Ember from 'ember';

import validators from 'lookit-base/utils/validators';

export default Ember.Controller.extend({
    session: Ember.inject.service(),

    selectedRaceIdentification: Ember.computed.alias('model.demographicsRaceIdentification'),
    today: new Date(),
    ageChoices: [
        'under 18',
        '18-21',
        '22-24',
        '25-29',
        '30-34',
        '35-39',
        '40-44',
        '45-49',
        '50-59',
        '60-69',
        '70 or over'
    ],
    childrenCounts: [
        '0',
        '1',
        '2',
        '3',
        '4',
        '5',
        '6',
        '7',
        '8',
        '9',
        '10',
        'More than 10'
    ],
    raceCategories: [
        'White',
        'Hispanic, Latino, or Spanish origin',
        'Black or African American',
        'Asian',
        'American Indian or Alaska Native',
        'Middle Eastern or North African',
        'Native Hawaiian or Other Pacific Islander',
        'Another race, ethnicity, or origin'
    ],
    genderOptions: [
        'male',
        'female',
        'other',
        'prefer not to answer'
    ],
    educationOptions: [
        'some or attending high school',
        'high school diploma or GED',
        'some or attending college',
        '2-year college degree',
        '4-year college degree',
        'some or attending graduate or professional school',
        'graduate or professional degree'
    ],
    spouseEducationOptions: [
        'some or attending high school',
        'high school diploma or GED',
        'some or attending college',
        '2-year college degree',
        '4-year college degree',
        'some or attending graduate or professional school',
        'graduate or professional degree',
        'not applicable - no spouse or partner'
    ],
    annualIncomeOptions: Ember.computed(function() {
        var ret = ['0', '5000', '10000', '15000'];
        for (var i = 20; i < 200; i += 10) {
            ret.push(`${i * 1000}`);
        }
        ret.push('over 200000');
        ret.push('prefer not to answer');

        return ret;
    }),
    guardianOptions: [
        '1',
        '2',
        '3 or more',
        'varies'
    ],
    yesNoOptions: [
        'no answer',
        'yes',
        'no'
    ],
    countryOptions: [
       	{"code":"AF", "country":"Afghanistan"},
		{"code":"AX", "country":"Åland Islands"},
		{"code":"AL", "country":"Albania"},
		{"code":"DZ", "country":"Algeria"},
		{"code":"AS", "country":"American Samoa"},
		{"code":"AD", "country":"Andorra"},
		{"code":"AO", "country":"Angola"},
		{"code":"AI", "country":"Anguilla"},
		{"code":"AQ", "country":"Antarctica"},
		{"code":"AG", "country":"Antigua and Barbuda"},
		{"code":"AR", "country":"Argentina"},
		{"code":"AM", "country":"Armenia"},
		{"code":"AW", "country":"Aruba"},
		{"code":"AU", "country":"Australia"},
		{"code":"AT", "country":"Austria"},
		{"code":"AZ", "country":"Azerbaijan"},
		{"code":"BS", "country":"Bahamas"},
		{"code":"BH", "country":"Bahrain"},
		{"code":"BD", "country":"Bangladesh"},
		{"code":"BB", "country":"Barbados"},
		{"code":"BY", "country":"Belarus"},
		{"code":"BE", "country":"Belgium"},
		{"code":"BZ", "country":"Belize"},
		{"code":"BJ", "country":"Benin"},
		{"code":"BM", "country":"Bermuda"},
		{"code":"BT", "country":"Bhutan"},
		{"code":"BO", "country":"Bolivia, Plurinational State of"},
		{"code":"BQ", "country":"Bonaire, Sint Eustatius and Saba"},
		{"code":"BA", "country":"Bosnia and Herzegovina"},
		{"code":"BW", "country":"Botswana"},
		{"code":"BV", "country":"Bouvet Island"},
		{"code":"BR", "country":"Brazil"},
		{"code":"IO", "country":"British Indian Ocean Territory"},
		{"code":"BN", "country":"Brunei Darussalam"},
		{"code":"BG", "country":"Bulgaria"},
		{"code":"BF", "country":"Burkina Faso"},
		{"code":"BI", "country":"Burundi"},
		{"code":"KH", "country":"Cambodia"},
		{"code":"CM", "country":"Cameroon"},
		{"code":"CA", "country":"Canada"},
		{"code":"CV", "country":"Cape Verde"},
		{"code":"KY", "country":"Cayman Islands"},
		{"code":"CF", "country":"Central African Republic"},
		{"code":"TD", "country":"Chad"},
		{"code":"CL", "country":"Chile"},
		{"code":"CN", "country":"China"},
		{"code":"CX", "country":"Christmas Island"},
		{"code":"CC", "country":"Cocos (Keeling) Islands"},
		{"code":"CO", "country":"Colombia"},
		{"code":"KM", "country":"Comoros"},
		{"code":"CG", "country":"Congo"},
		{"code":"CD", "country":"Congo, the Democratic Republic of the"},
		{"code":"CK", "country":"Cook Islands"},
		{"code":"CR", "country":"Costa Rica"},
		{"code":"CI", "country":"Côte d'Ivoire"},
		{"code":"HR", "country":"Croatia"},
		{"code":"CU", "country":"Cuba"},
		{"code":"CW", "country":"Curaçao"},
		{"code":"CY", "country":"Cyprus"},
		{"code":"CZ", "country":"Czech Republic"},
		{"code":"DK", "country":"Denmark"},
		{"code":"DJ", "country":"Djibouti"},
		{"code":"DM", "country":"Dominica"},
		{"code":"DO", "country":"Dominican Republic"},
		{"code":"EC", "country":"Ecuador"},
		{"code":"EG", "country":"Egypt"},
		{"code":"SV", "country":"El Salvador"},
		{"code":"GQ", "country":"Equatorial Guinea"},
		{"code":"ER", "country":"Eritrea"},
		{"code":"EE", "country":"Estonia"},
		{"code":"ET", "country":"Ethiopia"},
		{"code":"FK", "country":"Falkland Islands (Malvinas)"},
		{"code":"FO", "country":"Faroe Islands"},
		{"code":"FJ", "country":"Fiji"},
		{"code":"FI", "country":"Finland"},
		{"code":"FR", "country":"France"},
		{"code":"GF", "country":"French Guiana"},
		{"code":"PF", "country":"French Polynesia"},
		{"code":"TF", "country":"French Southern Territories"},
		{"code":"GA", "country":"Gabon"},
		{"code":"GM", "country":"Gambia"},
		{"code":"GE", "country":"Georgia"},
		{"code":"DE", "country":"Germany"},
		{"code":"GH", "country":"Ghana"},
		{"code":"GI", "country":"Gibraltar"},
		{"code":"GR", "country":"Greece"},
		{"code":"GL", "country":"Greenland"},
		{"code":"GD", "country":"Grenada"},
		{"code":"GP", "country":"Guadeloupe"},
		{"code":"GU", "country":"Guam"},
		{"code":"GT", "country":"Guatemala"},
		{"code":"GG", "country":"Guernsey"},
		{"code":"GN", "country":"Guinea"},
		{"code":"GW", "country":"Guinea-Bissau"},
		{"code":"GY", "country":"Guyana"},
		{"code":"HT", "country":"Haiti"},
		{"code":"HM", "country":"Heard Island and McDonald Islands"},
		{"code":"VA", "country":"Holy See (Vatican City State)"},
		{"code":"HN", "country":"Honduras"},
		{"code":"HK", "country":"Hong Kong"},
		{"code":"HU", "country":"Hungary"},
		{"code":"IS", "country":"Iceland"},
		{"code":"IN", "country":"India"},
		{"code":"ID", "country":"Indonesia"},
		{"code":"IR", "country":"Iran, Islamic Republic of"},
		{"code":"IQ", "country":"Iraq"},
		{"code":"IE", "country":"Ireland"},
		{"code":"IM", "country":"Isle of Man"},
		{"code":"IL", "country":"Israel"},
		{"code":"IT", "country":"Italy"},
		{"code":"JM", "country":"Jamaica"},
		{"code":"JP", "country":"Japan"},
		{"code":"JE", "country":"Jersey"},
		{"code":"JO", "country":"Jordan"},
		{"code":"KZ", "country":"Kazakhstan"},
		{"code":"KE", "country":"Kenya"},
		{"code":"KI", "country":"Kiribati"},
		{"code":"KP", "country":"Korea, Democratic People's Republic of"},
		{"code":"KR", "country":"Korea, Republic of"},
		{"code":"KW", "country":"Kuwait"},
		{"code":"KG", "country":"Kyrgyzstan"},
		{"code":"LA", "country":"Lao People's Democratic Republic"},
		{"code":"LV", "country":"Latvia"},
		{"code":"LB", "country":"Lebanon"},
		{"code":"LS", "country":"Lesotho"},
		{"code":"LR", "country":"Liberia"},
		{"code":"LY", "country":"Libya"},
		{"code":"LI", "country":"Liechtenstein"},
		{"code":"LT", "country":"Lithuania"},
		{"code":"LU", "country":"Luxembourg"},
		{"code":"MO", "country":"Macao"},
		{"code":"MK", "country":"Macedonia, the former Yugoslav Republic of"},
		{"code":"MG", "country":"Madagascar"},
		{"code":"MW", "country":"Malawi"},
		{"code":"MY", "country":"Malaysia"},
		{"code":"MV", "country":"Maldives"},
		{"code":"ML", "country":"Mali"},
		{"code":"MT", "country":"Malta"},
		{"code":"MH", "country":"Marshall Islands"},
		{"code":"MQ", "country":"Martinique"},
		{"code":"MR", "country":"Mauritania"},
		{"code":"MU", "country":"Mauritius"},
		{"code":"YT", "country":"Mayotte"},
		{"code":"MX", "country":"Mexico"},
		{"code":"FM", "country":"Micronesia, Federated States of"},
		{"code":"MD", "country":"Moldova, Republic of"},
		{"code":"MC", "country":"Monaco"},
		{"code":"MN", "country":"Mongolia"},
		{"code":"ME", "country":"Montenegro"},
		{"code":"MS", "country":"Montserrat"},
		{"code":"MA", "country":"Morocco"},
		{"code":"MZ", "country":"Mozambique"},
		{"code":"MM", "country":"Myanmar"},
		{"code":"NA", "country":"Namibia"},
		{"code":"NR", "country":"Nauru"},
		{"code":"NP", "country":"Nepal"},
		{"code":"NL", "country":"Netherlands"},
		{"code":"NC", "country":"New Caledonia"},
		{"code":"NZ", "country":"New Zealand"},
		{"code":"NI", "country":"Nicaragua"},
		{"code":"NE", "country":"Niger"},
		{"code":"NG", "country":"Nigeria"},
		{"code":"NU", "country":"Niue"},
		{"code":"NF", "country":"Norfolk Island"},
		{"code":"MP", "country":"Northern Mariana Islands"},
		{"code":"NO", "country":"Norway"},
		{"code":"OM", "country":"Oman"},
		{"code":"PK", "country":"Pakistan"},
		{"code":"PW", "country":"Palau"},
		{"code":"PS", "country":"Palestinian Territory, Occupied"},
		{"code":"PA", "country":"Panama"},
		{"code":"PG", "country":"Papua New Guinea"},
		{"code":"PY", "country":"Paraguay"},
		{"code":"PE", "country":"Peru"},
		{"code":"PH", "country":"Philippines"},
		{"code":"PN", "country":"Pitcairn"},
		{"code":"PL", "country":"Poland"},
		{"code":"PT", "country":"Portugal"},
		{"code":"PR", "country":"Puerto Rico"},
		{"code":"QA", "country":"Qatar"},
		{"code":"RE", "country":"Réunion"},
		{"code":"RO", "country":"Romania"},
		{"code":"RU", "country":"Russian Federation"},
		{"code":"RW", "country":"Rwanda"},
		{"code":"BL", "country":"Saint Barthélemy"},
		{"code":"SH", "country":"Saint Helena, Ascension and Tristan da Cunha"},
		{"code":"KN", "country":"Saint Kitts and Nevis"},
		{"code":"LC", "country":"Saint Lucia"},
		{"code":"MF", "country":"Saint Martin (French part)"},
		{"code":"PM", "country":"Saint Pierre and Miquelon"},
		{"code":"VC", "country":"Saint Vincent and the Grenadines"},
		{"code":"WS", "country":"Samoa"},
		{"code":"SM", "country":"San Marino"},
		{"code":"ST", "country":"Sao Tome and Principe"},
		{"code":"SA", "country":"Saudi Arabia"},
		{"code":"SN", "country":"Senegal"},
		{"code":"RS", "country":"Serbia"},
		{"code":"SC", "country":"Seychelles"},
		{"code":"SL", "country":"Sierra Leone"},
		{"code":"SG", "country":"Singapore"},
		{"code":"SX", "country":"Sint Maarten (Dutch part)"},
		{"code":"SK", "country":"Slovakia"},
		{"code":"SI", "country":"Slovenia"},
		{"code":"SB", "country":"Solomon Islands"},
		{"code":"SO", "country":"Somalia"},
		{"code":"ZA", "country":"South Africa"},
		{"code":"GS", "country":"South Georgia and the South Sandwich Islands"},
		{"code":"SS", "country":"South Sudan"},
		{"code":"ES", "country":"Spain"},
		{"code":"LK", "country":"Sri Lanka"},
		{"code":"SD", "country":"Sudan"},
		{"code":"SR", "country":"Suriname"},
		{"code":"SJ", "country":"Svalbard and Jan Mayen"},
		{"code":"SZ", "country":"Swaziland"},
		{"code":"SE", "country":"Sweden"},
		{"code":"CH", "country":"Switzerland"},
		{"code":"SY", "country":"Syrian Arab Republic"},
		{"code":"TW", "country":"Taiwan, Province of China"},
		{"code":"TJ", "country":"Tajikistan"},
		{"code":"TZ", "country":"Tanzania, United Republic of"},
		{"code":"TH", "country":"Thailand"},
		{"code":"TL", "country":"Timor-Leste"},
		{"code":"TG", "country":"Togo"},
		{"code":"TK", "country":"Tokelau"},
		{"code":"TO", "country":"Tonga"},
		{"code":"TT", "country":"Trinidad and Tobago"},
		{"code":"TN", "country":"Tunisia"},
		{"code":"TR", "country":"Turkey"},
		{"code":"TM", "country":"Turkmenistan"},
		{"code":"TC", "country":"Turks and Caicos Islands"},
		{"code":"TV", "country":"Tuvalu"},
		{"code":"UG", "country":"Uganda"},
		{"code":"UA", "country":"Ukraine"},
		{"code":"AE", "country":"United Arab Emirates"},
		{"code":"GB", "country":"United Kingdom"},
		{"code":"UM", "country":"United States Minor Outlying Islands"},
		{"code":"UY", "country":"Uruguay"},
		{"code":"UZ", "country":"Uzbekistan"},
		{"code":"VU", "country":"Vanuatu"},
		{"code":"VE", "country":"Venezuela, Bolivarian Republic of"},
		{"code":"VN", "country":"Viet Nam"},
		{"code":"VG", "country":"Virgin Islands, British"},
		{"code":"VI", "country":"Virgin Islands, U.S."},
		{"code":"WF", "country":"Wallis and Futuna"},
		{"code":"EH", "country":"Western Sahara"},
		{"code":"YE", "country":"Yemen"},
		{"code":"ZM", "country":"Zambia"},
		{"code":"ZW", "country":"Zimbabwe"}
    ],
    stateOptions: [
    	{"code":"AL", "state":"Alabama"},
		{"code":"AK", "state":"Alaska"},
		{"code":"AZ", "state":"Arizona"},
		{"code":"AR", "state":"Arkansas"},
		{"code":"CA", "state":"California"},
		{"code":"CO", "state":"Colorado"},
		{"code":"CT", "state":"Connecticut"},
		{"code":"DE", "state":"Delaware"},
		{"code":"DC", "state":"District Of Columbia"},
		{"code":"FL", "state":"Florida"},
		{"code":"GA", "state":"Georgia"},
		{"code":"HI", "state":"Hawaii"},
		{"code":"ID", "state":"Idaho"},
		{"code":"IL", "state":"Illinois"},
		{"code":"IN", "state":"Indiana"},
		{"code":"IA", "state":"Iowa"},
		{"code":"KS", "state":"Kansas"},
		{"code":"KY", "state":"Kentucky"},
		{"code":"LA", "state":"Louisiana"},
		{"code":"ME", "state":"Maine"},
		{"code":"MD", "state":"Maryland"},
		{"code":"MA", "state":"Massachusetts"},
		{"code":"MI", "state":"Michigan"},
		{"code":"MN", "state":"Minnesota"},
		{"code":"MS", "state":"Mississippi"},
		{"code":"MO", "state":"Missouri"},
		{"code":"MT", "state":"Montana"},
		{"code":"NE", "state":"Nebraska"},
		{"code":"NV", "state":"Nevada"},
		{"code":"NH", "state":"New Hampshire"},
		{"code":"NJ", "state":"New Jersey"},
		{"code":"NM", "state":"New Mexico"},
		{"code":"NY", "state":"New York"},
		{"code":"NC", "state":"North Carolina"},
		{"code":"ND", "state":"North Dakota"},
		{"code":"OH", "state":"Ohio"},
		{"code":"OK", "state":"Oklahoma"},
		{"code":"OR", "state":"Oregon"},
		{"code":"PA", "state":"Pennsylvania"},
		{"code":"RI", "state":"Rhode Island"},
		{"code":"SC", "state":"South Carolina"},
		{"code":"SD", "state":"South Dakota"},
		{"code":"TN", "state":"Tennessee"},
		{"code":"TX", "state":"Texas"},
		{"code":"UT", "state":"Utah"},
		{"code":"VT", "state":"Vermont"},
		{"code":"VA", "state":"Virginia"},
		{"code":"WA", "state":"Washington"},
		{"code":"WV", "state":"West Virginia"},
		{"code":"WI", "state":"Wisconsin"},
		{"code":"WY", "state":"Wyoming"},
		{"code":"AA", "state":"Armed Forces Americas"},
		{"code":"AP", "state":"Armed Forces Pacific"},
		{"code":"AE", "state":"Armed Forces Others"}
    ],
    densityOptions: [
        "urban",
        "suburban",
        "rural"
    ],

    isValid: Ember.computed('model.demographicsNumberOfBooks', function() {
        return validators.min(0)(this.get('model.demographicsNumberOfBooks'));
    }),

    nNumberOfChildren: 11,
    numberOfChildren: Ember.computed('nNumberOfChildren', 'model.demographicsNumberOfChildren', function() {
        var numberOfChildren = this.get('model.demographicsNumberOfChildren');
        if (!numberOfChildren) {
            return 0;
        } else if (isNaN(numberOfChildren)) {
            numberOfChildren = this.get('nNumberOfChildren');
            if (!numberOfChildren) {
                return 0;
            } else {
                return parseInt(numberOfChildren);
            }
        } else {
            return parseInt(numberOfChildren);
        }
    }),
    onNumberOfChildrenChange: Ember.observer('numberOfChildren', function() {
        var numberOfChildren = this.get('numberOfChildren');
        var birthdays = [];
        for (var i = 0; i < numberOfChildren; i++) {
            birthdays[i] = this.get('model.demographicsChildBirthdays').objectAt(i);
        }
        this.get('model.demographicsChildBirthdays').setObjects(birthdays);
    }),
    childBirthdays: Ember.computed('model.demographicsChildBirthdays.[]', {
        get: function() {
            var ret = Ember.Object.create();
            this.get('model.demographicsChildBirthdays').toArray().forEach(function(bd, i) {
                ret.set(i.toString(), bd);
            });
            return ret;
        },
        set: function(_, birthdays) {
            var ret = [];
            Object.keys(birthdays).forEach(function(key) {
                ret[parseInt(key)] = birthdays[key];
            });
            this.get('model.demographicsChildBirthdays').setObjects(ret);
            this.propertyDidChange('childBirthdays');
            return this.get('childBirthdays');
        }
    }),
    actions: {
        selectRaceIdentification: function(item) {
            var selectedRaceIdentification = this.get('selectedRaceIdentification') || [];
            if (item.checked) {
                if (selectedRaceIdentification.indexOf(item.value) === -1) {
                    selectedRaceIdentification.push(item.value);
                }
            } else {
                selectedRaceIdentification = selectedRaceIdentification.filter(i => i !== item.value);
            }
            this.set('selectedRaceIdentification', selectedRaceIdentification);
        },
        saveDemographicsPreferences: function() {
            this.get('model').save().then(() => {
                this.toast.info('Demographic survey saved successfully.');
            });
        },
        setChildBirthday(index, birthday) {
            var childBirthdays = this.get('childBirthdays');
            childBirthdays.set(index.toString(), birthday);
            this.set('childBirthdays', childBirthdays);
        }
    }
});
