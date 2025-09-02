<?php

$config = array(

    'admin' => array(
        'core:AdminPassword',
    ),

    // Creates a user with username: 'certbot' and password: 'password'
    // includes fullname and lp_teams keys just as Ubuntu One schema would
    'example-userpass' => array(
        'exampleauth:UserPass',
        'certbot:password' => array(
            'fullname' => 'Certification Bot',
            'lp_teams' => array('canonical-hw-cert'),
            'email' => 'certbot@canonical.com'
        ),
        'mark:password' => array(
            'fullname' => 'Mark',
            'lp_teams' => array('canonical'),
            'email' => 'mark@electricdemon.com'
        ),
    ),

);