import Ember from 'ember';

export default Ember.Route.extend({
    sessionAccount: Ember.inject.service(),

    model(params) {
        return this.store.findRecord('experiment', params.experiment_id);
    },

    setupController(controller) {
        this._super(...arguments);
        this.get('sessionAccount').load()
            .then(user => controller.set('account', user));
    },

    resetController: function(controller, isExiting) {
        if (isExiting) {
            controller.set('selectedChildId', null);
        }
    }
});
