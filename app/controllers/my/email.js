import Ember from 'ember';

export default Ember.Controller.extend({
    toast: Ember.inject.service(),
    sessionAccount: Ember.inject.service('session-account'),
    suppressions: null,
    canSave: true,
    actions: {
        saveEmailPreferences: function() {
            var suppressions = this.get('suppressions');
            this.set('canSave', false);
            this.get('sessionAccount').loadCurrentUser().then(account => {
                var suppressionsHash = {};
                Object.keys(suppressions).forEach(s => {
                    var suppression = suppressions[s];
                    suppressionsHash[`${suppression.id}`] = !suppression.subscribed;
                });
                account.setSuppressions(suppressionsHash).then(() => {
                    this.set('canSave', true);
                    this.get('toast').info('Notification preferences saved successfully');
                });
            });
        }
    }
});
