import Ember from 'ember';

export default Ember.Route.extend({
    model() {
        let Experiment = this.store.modelFor('experiment');
        return this.store.query('experiment', {
            q:`state:${Experiment.prototype.ACTIVE}`
        });
    }
});
