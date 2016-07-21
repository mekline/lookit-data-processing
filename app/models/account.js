import Ember from 'ember';
import DS from 'ember-data';
import Account from 'exp-models/models/account';

import config from 'ember-get-config';

const DEMOGRAPHIC_FIELDS = ['demographicsLanguagesSpokenAtHome', 'demographicsNumberOfChildren', 'demographicsNumberOfGuardians', 'demographicsNumberOfGuardiansExplanation', 'demographicsRaceIdentification', 'demographicsAge', 'demographicsGender', 'demographicsEducationLevel', 'demographicsSpouseEducationLevel', 'demographicsAnnualIncome', 'demographicsWillingToBeContactedForSimilarStudies', 'demographicsCanScheduleAnAppointment', 'demographicsNumberOfBooks', 'demographicsAdditionalComments'];

const ASM_MAPPING = {
    nextSession: {
        label: 'Next Session',
        description: 'It\'s time for another session of a study we are currently participating in',
        id: '911'
    },
    newStudies: {
        label: 'New Studies',
        description: 'A new study is available for one of my children',
        id: '913'
    },
    resultsPublished: {
        label: 'Results Published',
        description: 'The results of a study we participated in are published',
        id: '915'
    },
    optOut: {
        label: 'Opt Out',
        description: 'A researcher may also email you personally if we have questions about your responses (for example, if you report two different birthdates for a child and we\'re not sure whether he\'s 3 or 5) or if you report a technical problem. Check here to opt out:',
        id: '1117'
    }
};

export default Account.extend({
    email: DS.attr('string'),
    mustResetPassword: DS.attr('boolean'),

    demographicsNumberOfChildren: DS.attr('string'),
    demographicsChildBirthdays: DS.attr('dateList'),
    demographicsLanguagesSpokenAtHome: DS.attr('string'),
    demographicsNumberOfGuardians: DS.attr('string'),
    demographicsNumberOfGuardiansExplanation: DS.attr('string'),
    demographicsRaceIdentification: DS.attr(),
    demographicsAge: DS.attr('string'),
    demographicsGender: DS.attr('string'),
    demographicsEducationLevel: DS.attr('string'),
    demographicsSpouseEducationLevel: DS.attr('string'),
    demographicsAnnualIncome: DS.attr('string'),
    demographicsWillingToBeContactedForSimilarStudies: DS.attr('string'),
    demographicsCanScheduleAnAppointment: DS.attr('string'),
    demographicsNumberOfBooks: DS.attr('number'),
    demographicsAdditionalComments: DS.attr('string'),

    hasCompletedSurvey: Ember.computed.or(...DEMOGRAPHIC_FIELDS),

    suppressionsUrl: Ember.computed('email', function() {
        var groups = Object.keys(ASM_MAPPING).map(key => {
            return `group[]=${ASM_MAPPING[key].id}`;
        }).join('&');
        return `${config.JAMDB.url}/v1/id/collections/${config.JAMDB.namespace}.accounts/user?id=${this.get('id')}&${groups}`;
    }),
    getSuppressions() {
        var url = this.get('suppressionsUrl');
        var adapter = this.store.adapterFor('application');
        return adapter.ajax(
            url,
            'GET',
            adapter.ajaxOptions(
                url,
                'GET'
            )
        ).then(res => {
            return Object.keys(ASM_MAPPING).map(key => {
                var group = ASM_MAPPING[key];
                group.attr = key;
                group.subscribed = !res.data.attributes[group.id];
                if (key === 'optOut') {
                    group.subscribed = !group.subscribed;
                }
                return group;
            });
        });
    },
    setSuppressions(suppressionsHash) {
        suppressionsHash.id = this.get('id');
        suppressionsHash[ASM_MAPPING.optOut.id] = !suppressionsHash[ASM_MAPPING.optOut.id];
        var url = this.get('suppressionsUrl');
        var adapter = this.store.adapterFor('application');
        return adapter.ajax(
            url,
            'PATCH', {
                data: {
                    data: {
                        type: "supressions",
                        attributes: suppressionsHash
                    }
                }
            }
        ).then(res => {
            return Object.keys(ASM_MAPPING).map(key => {
                var group = JSON.parse(JSON.stringify(ASM_MAPPING[key]));
                group.attr = key;
                group.subscribed = !res.data.attributes[group.id];
                return group;
            });
        });
    }
});
