import Ember from 'ember';
import ENV from 'lookit-base/config/environment';

export default Ember.Component.extend({
    namespace: ENV.JAMDB.namespace,
    collection: ENV.JAMDB.collection,

    username: null,
    password: null,
    email: null,

    maySubmit: Ember.computed.and('username', 'password', 'email'),

    actions: {
        createAccount() {
            this.get('create')({
                username: this.get('username'),
                password: this.get('password'),
                email: this.get('email')
            });
            return false;
        }
    }
});
