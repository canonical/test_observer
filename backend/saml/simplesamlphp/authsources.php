<?php

$config = array(

    'admin' => array(
        'core:AdminPassword',
    ),

    'example-userpass' => array(
        'exampleauth:UserPass',
        'certbot:password' => array(
            'fullname' => 'Certification Bot',
            'lp_teams' => array('canonical-hw-cert'),
            'email' => 'certbot@canonical.com'
        ),
    ),

);