import Ember from 'ember';
// Do we want/need this?
import AuthenticatedRouteMixin from 'ember-simple-auth/mixins/authenticated-route-mixin';

import ExpPlayerRouteMixin from 'exp-player/mixins/exp-player-route';
import WarnOnExitRouteMixin from 'exp-player/mixins/warn-on-exit-route';

const { service } = Ember.inject;

export default Ember.Route.extend(AuthenticatedRouteMixin, ExpPlayerRouteMixin, WarnOnExitRouteMixin, {
    sessionAccount: service('session-account'),

    _getExperiment(params) {
        return this.store.findRecord('experiment', Ember.get(params, 'experiment_id'));
    },
    beforeModel (transition) {
        if (!this.get('sessionAccount.profile')) {
            this.transitionTo('studies.detail', transition.params.participate.experiment_id);
        }
        return this._super(...arguments);
    }
});
