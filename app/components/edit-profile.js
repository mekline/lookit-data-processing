import Ember from 'ember';

export default Ember.Component.extend({
    today: new Date(),

    tooltips: {
        firstName: 'This lets you select the correct child to participate in a particular study. A nickname or initials are fine! We may include your child\'s name in email to you (for instance, "There\'s a new study available for Molly!") but will never publish names or use them in our research.',
        birthday: 'This lets us figure out exactly how old your child when he or she participates in a study. We never publish children\'s birthdates or information that would allow a reader to calculate the birthdate.'
    },
    deleting: false,

    profile: null,
    account: null,
    isDirty: Ember.computed.alias('profile.hasDirtyAttributes'),
    isValid: Ember.computed('profile.firstName', 'profile.birthday', 'profile.gender', 'profile.ageAtBirth', function() {
        if (!Ember.isEmpty(this.get('profile.firstName')) && !Ember.isEmpty(this.get('profile.birthday')) && !Ember.isEmpty(this.get('profile.gender')) && !Ember.isEmpty(this.get('profile.ageAtBirth'))) {
            return true;
        }
        return false;
    }),
    genderOptions: [
        'male',
        'female',
        'other or prefer not to answer'
    ],
    ageAtBirthOptions: Ember.computed(function() {
        var options = ['Not sure or prefer not to answer'];
        options.push('Under 24 weeks');
        for (var i = 24; i < 40; i++) {
            options.push(`${i} weeks`);
        }
        options.push('40 or more weeks');
        return options;
    }),
    actions: {
        save: function(profile) {
            var account = this.get('account');
            var verb = 'updated';
            if (account.get('profiles').indexOf(profile) === -1) {
                profile.set('profileId', account.generateProfileId());
                account.get('profiles').unshiftObject(profile);
                verb = 'added';
                this.get('onAdd')();
            }

            this.get('account').save().then(() => {
                profile.save();
                this.toast.info(`Child profile ${verb} successfully.`);
            });
        },
        cancel: function(profile) {
            profile.rollbackAttributes();
        },
        cancelAdd: function() {
            this.get('onCancelAdd')();
        },
        delete: function(profile) {
            profile.set('deleted', true);
            this.get('account').save().then(() => {
                this.toast.info(`${profile.get('firstName')}'s profile deleted successfully.`);
            });
        },
        showDelete: function() {
            this.toggleProperty('deleting');
        }
    }
});
