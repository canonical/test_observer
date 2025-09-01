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
        'omar-selo:password' => array(
            'fullname' => 'Omar Abou Selo',
            'lp_teams' => array('canonical'),
            'email' => 'omar.selo@canonical.com'
        ),
    ),

);