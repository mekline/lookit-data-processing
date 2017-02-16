import Ember from 'ember';

export default Ember.Controller.extend({
    toast: Ember.inject.service(),

    suppressions: null,
    _setSuppressions() {
        if (this.get('model')) {
            this.get('model').getSuppressions().then(suppressions => {
                this.set('suppressions', suppressions);
            });
        }
    },
    init() {
        this._super(...arguments);
        this._setSuppressions();
    },
    onAccountChange: Ember.observer('model', function () {
        this._setSuppressions();
    }),
    canSave: true,
    actions: {
        saveEmailPreferences: function () {
            var suppressions = this.get('suppressions');
            this.set('canSave', false);
            let account = this.get('model');
            var suppressionsHash = {};
            suppressions.forEach(s => {
                suppressionsHash[`${s.id}`] = !s.subscribed;
            });
            account.setSuppressions(suppressionsHash).then(() => {
                this.get('toast').info('Notification preferences saved successfully');
            }).catch(() => this.get('toast').error('Could not update notification preferences. If the problem persists, please contact support.')
            ).finally(() => this.set('canSave', true));
        }
    }
});
