import Ember from 'ember';

export default Ember.Component.extend({
    session: Ember.inject.service(),
    sessionAccount: Ember.inject.service(),

    /**
     * @method logout A passed in closure action
     */
    logout: null,

    // Placeholder: account will be set when session auth state changes
    account: null,
    accountName: Ember.computed.alias('account.username'),

    init() {
        this._super(...arguments);
        this._fetchAccount();
    },

    _fetchAccount() {
        if (!this.get('session.isAuthenticated')) {
            this.set('account', null);
        } else {
            this.get('sessionAccount').load()
                .then(account => this.set('account', account))
                .catch(() => this.set('account', null));
        }
    },

    updateAccount: Ember.observer('session.isAuthenticated', function () {
        this._fetchAccount();
    })
});
