import Ember from 'ember';
import AuthenticatedRouteMixin from 'ember-simple-auth/mixins/authenticated-route-mixin';

import esaConfig from 'ember-simple-auth/configuration';

export default Ember.Route.extend(AuthenticatedRouteMixin, {
    session: Ember.inject.service(),
    sessionAccount: Ember.inject.service(),

    model() {
        return this.get('sessionAccount').load();
    },
    beforeModel(transition) {
        let token = transition.queryParams.access_token;
        if (this.get('session.isAuthenticated') || !token) {
            // Either user is authenticated, or no token is present- either way, auth mixin should act normally
            return this._super(...arguments);
        } else {
            // User is unauthenticated, but a token is present- we must bypass ESA so that user is automatically
            //   logged in but remains on this page. (avoid race conditions between sessionAuthenticated events and super call)
            transition.abort();
            this.set('session.attemptedTransition', transition);
            return this.get('session')
                .authenticate('authenticator:jam-jwt', {}, token)
                .then(() => window.location.hash = '')
                .catch(() => this.transitionTo(esaConfig.authenticationRoute));


        }
    }
});
