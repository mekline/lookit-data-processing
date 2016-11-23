import Ember from 'ember';
import ENV from 'lookit-base/config/environment';
import BaseAuthenticator from 'ember-simple-auth/authenticators/base';

import { jwt_decode } from 'ember-cli-jwt-decode';

import moment from 'moment';

const {
    $, RSVP
} = Ember;

export default BaseAuthenticator.extend({
    url: `${ENV.JAMDB.url}/v1/auth`,

    raven: Ember.inject.service(),

    _captureUser(username) {
        this.get('raven').callRaven('setUserContext', { id: username });
    },

    _verifyToken(token) {
        // For now we will trust the token given without validating against the server, provided it is well-formed
        //   and can be parsed- but we will sanity check that it is still active. This will prevent auth/restore errors.
        return token.exp > moment().unix();
    },

    restore(data) {
        let token;
        try {
            token = JSON.parse(atob(data.token.split('.')[1]));
        } catch (e) {
            return RSVP.reject();
        }

        if (this._verifyToken(token)) {
            this._captureUser(data.id);
            return RSVP.resolve(data);
        }
        return RSVP.reject(data);
    },

    authenticate(attrs, token) {
        // Can authenticate either using an object with username and password, OR a pre-provided JWT token string
        if (token) {
            return new Ember.RSVP.Promise((resolve, reject) => {
                var payload;
                var accountId;
                try { // Handle case where token is malformed- otherwise ember swallows the error
                    payload = jwt_decode(token);
                    accountId = payload.sub.split('-').pop();
                } catch (e) {
                    reject();
                }
                if (!this._verifyToken(payload)) {
                    reject();
                }

                this._captureUser(accountId);
                resolve({
                    id: accountId,
                    token: token
                });
            });
        }
        let jqDeferred = $.ajax({
            method: 'POST',
            url: this.url,
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                data: {
                    type: 'users',
                    attributes: attrs
                }
            })
        }).then(res => {
            // Include logged-in user data with all Raven payloads during session
            this._captureUser(res.id);
            return res.data.attributes;
        });

        return new Ember.RSVP.Promise((resolve, reject) => {
            jqDeferred.done(resolve);
            jqDeferred.fail(reject);
        });
    },

    invalidate() {
        // Clear the Raven user context when the user logs out
        return this._super(...arguments).then(() => this._captureUser());
    }
});
