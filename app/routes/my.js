import Ember from 'ember';
import AuthenticatedRouteMixin from 'ember-simple-auth/mixins/authenticated-route-mixin';

const {
    service
} = Ember.inject;

export default Ember.Route.extend(AuthenticatedRouteMixin, {
    session: service('session'),
    sessionAccount: service('session-account'),

    model() {
        return this.get('sessionAccount').loadCurrentUser();
    },
    beforeModel(transition) {
        if (transition.queryParams.access_token) {
            return this.get('session')
                .authenticate('authenticator:jam-jwt', {}, transition.queryParams.access_token)
                .then(() => {
                    window.location.hash = '';
		    return this._super(...arguments);
                });
        }
	return this._super(...arguments);
    }
});
