import Ember from 'ember';

/**
 * @module lookit
 * @submodule services
 */

/**
 * A service for accessing information about the currently logged-in user
 * @class sessionAccount
 */
export default Ember.Service.extend({
    session: Ember.inject.service(),
    store: Ember.inject.service(),

    profile: Ember.computed.alias('session.data.profile'),

    currentUserId: Ember.computed('session.data.authenticated', function() {
        var session = this.get('session');
        if (session.get('isAuthenticated')) {
            return session.get('data.authenticated.id');
        } else {
            return null;
        }
    }),
    /**
     * Fetch information about the currently logged in user. If no user is logged in, this method returns a rejected promise.
     * @method load
     * @return {Ember.RSVP.Promise}
     */
    load() {
        return new Ember.RSVP.Promise((resolve, reject) => {
            var currentUserId = this.get('currentUserId');
            if (!Ember.isEmpty(currentUserId)) {
                var currentUser = this.get('store').peekRecord('account', currentUserId);
                if (currentUser) {
                    resolve(currentUser);
                } else {
                    this.get('store').findRecord('account', currentUserId).then(resolve, reject);
                }
            } else {
                reject();
            }
        });
    }
});
