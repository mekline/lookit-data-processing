import Ember from 'ember';

import {expStates} from 'exp-models/models/experiment';

export default Ember.Route.extend({
    model() {
        return this.store.query('experiment', {
            q:`state:${expStates.ACTIVE}`
        });
    }
});
