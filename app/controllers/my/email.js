import Ember from 'ember';

export default Ember.Controller.extend({
    toast: Ember.inject.service(),
    sessionAccount: Ember.inject.service('session-account'),
    account: Ember.computed.alias('sessionAccount.account'),
    suppressions: null,
    _setSuppressions() {
	if (this.get('account')) {
	    this.get('account').getSuppressions().then(suppressions => {
		this.set('suppressions', suppressions);
	    });
	}
    },
    init() {
	this._super(...arguments);
	this._setSuppressions();
    },
    onAccountChange: Ember.observer('account', function() {
	this._setSuppressions();
    }),
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
