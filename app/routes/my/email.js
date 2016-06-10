import Ember from 'ember';
import AuthenticatedRouteMixin from 'ember-simple-auth/mixins/authenticated-route-mixin';

export default Ember.Route.extend(AuthenticatedRouteMixin, {
    sessionAccount: Ember.inject.service('session-account'),
    model() {
        return this.get('sessionAccount').loadCurrentUser();
    },
    setupController(controller, model) {
        model.getSuppressions().then(suppressions => {
            controller.set('suppressions', suppressions);
        });
    }
});
