---
layout: default
title: Home
---

## Andrew Young

![Dr Andrew Young](assets/images/Andy.jpg)

Andrew Young is an Associate Professor in the School of Physics at the University of Bristol. His research interests include numerical and observational astrophysics focused on accreting black holes. The numerical work involves the development of general relativistic models of the time-dependent spectra of accretion flows with different disc, corona, and spacetime geometries. The observational work concerns the analysis of X-ray data from accreting black holes using telescopes such as *XMM-Newton*, *Chandra*, and *NuSTAR*.

## Latest news

<ul>
  {% for post in site.posts limit: 3 %}
    <li>
      <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
      {{ post.excerpt }}
    </li>
  {% endfor %}
</ul>

## Group members

| Name | Position |
| --- | --- |
| [Fergus Baker](https://research-information.bris.ac.uk/en/persons/fergus-baker) | PhD student (primary supervisor) |
| [Gloria Raharimbolamena](https://research-information.bris.ac.uk/en/persons/gloria-raharimbolamena) | PhD student (primary supervisor) |
| [Tom Higginson](https://research-information.bris.ac.uk/en/persons/tom-s-higginson) | PhD student (co-supervisor) |
| [Yara Simango](https://research-information.bris.ac.uk/en/persons/yara-h-simango) | PhD student (co-supervisor) |

I am also secondary supervisor for students who are not working on extragalactic astronomy.
